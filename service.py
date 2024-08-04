import os
import PyPDF2
from docx import Document
from fastapi import UploadFile
from user import User
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import OpenAI
from langchain_openai import AzureOpenAI
from langchain_groq import ChatGroq
import pickle
from datetime import datetime
import io
from dotenv import load_dotenv
import threading
from sentence_transformers import SentenceTransformer
import torch
import json
from booking import Booking

USER_STORE = {}

functions = {
    "I want to book. Can you book me? I want to do reservation. Can you get my reservation?": "BOOK",
    "I have a question. Can you answer my question? I want to ask. Ask about. My question is.": "QUESTION"
}

models = {}
class BackgroundTasks(threading.Thread):
    def run(self):
        try:
            model = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
            encoder = SentenceTransformer(model, cache_folder='./encoder')
            models["model"] = model
            models["encoder"] = encoder
        except Exception as e:
            print(f"Error loading model: {e}")

thread = BackgroundTasks()
thread.start()


async def upload_documents(user: User, files: list[UploadFile], password:str) -> tuple[str, int]:
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    if password != ADMIN_PASSWORD:
        return "Only ADMIN can insert files.", 400
    text = await _extract_text_from_document(files)
    chunks = await _chunk_text(text)
    await _create_embeddings_and_save(user, chunks)
    return "Document is uploaded successfully.", 200


async def _extract_text_from_document(files: list[UploadFile]) -> str:
    text = ""
    for file in files:
        byte_object = await file.read()
        file_name = file.filename
        file_extension = os.path.splitext(file_name)[1]
        if file_extension == '.txt':
            text += byte_object.decode('utf-8')
        elif file_extension == '.pdf':
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(byte_object))
            for page_number in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_number]
                text += page.extract_text()
        elif file_extension == '.docx':
            doc = Document(io.BytesIO(byte_object))
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
    return text


async def _chunk_text(text: str) -> list[str]:
    chunks = None
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=512,
        chunk_overlap=10,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


async def _create_embeddings_and_save(user: User, chunks: any) -> FAISS:
    embeddings = HuggingFaceEmbeddings(model_name=user.embedder)
    pkl_name = os.path.join(user.username + ".pkl")
    vector_store = FAISS.from_texts(chunks, embeddings, metadatas=[{"source": f"{pkl_name}:{i}"} for i in range(len(chunks))])
    with open(pkl_name, "wb") as f:
        pickle.dump(vector_store, f)
    return vector_store


async def ask_question(user: User, question: str) -> tuple[str, int]: 
    
    user = await _get_saved_user(user)

    encoder = models["encoder"]
    question_embedding = encoder.encode(question)
    
    similarities = {}
    for function, answer in functions.items():
        description_embedding = encoder.encode(answer)
        cosine_sim = torch.nn.CosineSimilarity(dim=0, eps=1e-6)
        request_embedding_tensor = torch.tensor(question_embedding)
        description_embedding_tensor = torch.tensor(description_embedding)
        similarity = cosine_sim(request_embedding_tensor, description_embedding_tensor)
        similarities[function] = similarity.item()
    
    max_similarity = max(similarities.values())
    max_similarity_function = max(similarities, key=similarities.get)

    if max_similarity < 0.2:
        return "I could not understand what you really meant by that. Is it possible for you to give more details ?", 400
    elif max_similarity_function == "BOOK":
        final_answer, memory, system_message, http_code = await _book(user, question)
    else:
        final_answer, memory, system_message, http_code = await _rag(user, question)

    print(f"[DEBUG] Selected Function: {max_similarity_function}")
    
    user.memory.save(question=question, answer=final_answer)
    await _log(user=user, memory=memory, question=question, system_message=system_message, selected_function= max_similarity_function, answer= answer, final_answer = final_answer)

    return final_answer, http_code

async def _book(user: User, question: str):

    system_message = """
    You are responsible for getting a reservation information and creating a json from it.
    Do not give any other response than JSON.
    Detect the required json fields and put them in the right place.
    
    You need to find following values in the text and put in the JSON:
    full_name: The full name of the customer,
    phone_number: The phone number of the customer,
    e_mail: The e-mail of the customer,
    start_date: The arrival date of the customer,
    end_date: The leaving date of the customer,
    guest_count: The customer count,
    room_type: What type of room they will stay,
    rumber_of_rooms: How many rooms they want,
    payment_method: How they will pay,
    include_breakfast: Do they want to include breakfast as well or not,
    extra_details: (Optional) other informations

    Do NOT forget:
    Dates must be in YYYY-MM-DD format.
    End date must be after start date.
    Guest count must be at least 1.
    Number of rooms must be at least 1.
    Phone number must be between 10 and 15 digits.
    Include breakfast must be a boolean.

    <Example>
    <Human>:
    Hi, I am Barkın Özer. You can call me from 5365363636 or mail me at c.barkinozer@gmail.com, We plan to be there at 15 August 2024 between 00.00 pm to 02.00 pm and leave at the 24 th.
    Me and my girlfriend will stay on an economy room. I am planning to pay with visa card. We want breakfasts as well. Please include that.
    Also can you add spa to our gym plan as well? Thanks.

    <AI>:
    fields = {
        "full_name": "Barkın Özer",
        "phone_number": "5365363636",
        "email": "c.barkinozer@gmail.com",
        "start_date": "2024-08-15",
        "end_date": "2024-08-24",
        "guest_count": 2,
        "room_type": "Economy Room",
        "number_of_rooms": 1,
        "payment_method": "credit card",
        "include_breakfast": True,
        "extra_detail": "Visa card will be used as credit card. Spa will be added to the gym plan. Planning to arrive between 00.00 pm to 02.00 pm."
    }

    Now it's your turn:
    """
    memory = user.memory.get_memory()
    prompt = f" System Message: {system_message} <Question>: {question} <Memory>: {memory}"
    print("[DEBUG] Memory: ", memory)
    
    json_string = _ask_llm(user=user, prompt=prompt)
    
    data = json.loads(json_string)
    
    full_name = data['full_name']
    phone_number = data['phone_number']
    email = data['email']
    start_date = data['start_date']
    end_date = data['end_date']
    guest_count = data['guest_count']
    room_type = data['room_type']
    number_of_rooms = data['number_of_rooms']
    payment_method = data['payment_method']
    include_breakfast = data['include_breakfast']
    extra_details = data['extra_details']

    is_booking_valid = False

    booking = Booking(full_name=full_name, phone_number=phone_number, email=email, start_date=start_date, end_date=end_date, guest_count=guest_count, room_type=room_type, number_of_rooms=number_of_rooms, payment_method=payment_method, include_breakfast=include_breakfast, extra_details=extra_details)
    is_booking_valid, validation_message = booking.is_valid()

    if not is_booking_valid:
        system_message = """
        You are a json fixer.
        Your goal is to fix the values in the json accordding to the validation message you will receive.

        <Example>
        <Question>:
        Hi, I am Barkın Özer. You can call me from 5365363636 or mail me at c.barkinozer@gmail.com, We plan to be there at 15 August 2024 between 00.00 pm to 02.00 pm and leave at the 22 th.
        Me and my girlfriend will stay on an economy room. I am planning to pay with visa card. We want breakfasts as well. Please include that.
        Also can you add spa to our gym plan as well? Thanks.
        <JSON>:
        fields = {
            "full_name": "Barkın Özer",
            "phone_number": "5365363636",
            "email": "c.barkinozer@gmail.com",
            "start_date": "15 August 2022",
            "end_date": "22th",
            "guest_count": 2,
            "room_type": "Economy Room",
            "number_of_rooms": 0,
            "payment_method": "visa card",
            "include_breakfast": "Yes",
        }
        <Validation Message>:
        Dates must be in YYYY-MM-DD format.

        <AI>:
        fields = {
            "full_name": "Barkın Özer",
            "phone_number": "5365363636",
            "email": "c.barkinozer@gmail.com",
            "start_date": "2024-08-15",
            "end_date": "2024-08-22",
            "guest_count": 2,
            "room_type": "Economy Room",
            "number_of_rooms": 1,
            "payment_method": "credit card",
            "include_breakfast": True,
            "extra_detail": "Visa card will be used as credit card. Spa will be added to the gym plan. Planning to arrive between 00.00 pm to 02.00 pm."
        }
        
        Now, it's your turn:
        """
        prompt = f" System Message: {system_message}\n <Question>: {question}\n <JSON>: {json_string}\n <Validation Message>: {validation_message}\n"
        json_string = _ask_llm(user=user, prompt=prompt)
        booking = Booking(full_name=full_name, phone_number=phone_number, email=email, start_date=start_date, end_date=end_date, guest_count=guest_count, room_type=room_type, number_of_rooms=number_of_rooms, payment_method=payment_method, include_breakfast=include_breakfast, extra_details=extra_details)
        is_booking_valid, validation_message = booking.is_valid()

    if not is_booking_valid:
        return f"Booking validation is not met: f{validation_message}", 400
    return "", 200

async def _get_saved_user(user: User) -> User:
    if user.username in USER_STORE:
        return USER_STORE[user.username]
    else:
        USER_STORE[user.username] = user
        return user


async def _rag(user: User, question: str, api_key: str):
    vector_store = await _get_vector_file(user.username)
    if vector_store is None:
        return "Document not found.", None, None, 400
    
    os.environ["GOOGLE_API_KEY"] = api_key
    
    llm = await _get_llm(model_name=user.llm)
    memory = user.memory.get_memory()
    docs = vector_store.similarity_search(question+memory)
    retrieved_chunks = docs[0].page_content + docs[1].page_content + docs[2].page_content
    system_message="Figure out the answer of the question by the given information pieces. ALWAYS answer with the language of the question."
    prompt = system_message + "Question: " + question + " Context: " + retrieved_chunks
    try:
        response = llm.invoke(prompt)
    except Exception:
        return "Wrong API key.", None, None, 400
    answer = response.content + "  **<Most Related Chunk>**  " + retrieved_chunks
    print(f"[DEBUG] RAG Results: {answer}")

    system_message = """
    You are a reservation assistant who books and reserves places.
    Your task is to answer the questions asked by the user using the information provided to you.
    The tone of your answers is friendly and neutral.
    Your response should be at least a few sentences long.
    NEVER use information outside of what is provided to you.

    <Example 1>:
    <Human>:
    <Question>:
    I need a gym? Is it extra?
    <Information>:
    Yes, our fitness center is open 24/7 and is available for all guests.
    <Memory>:
    <AI>:
    Yes, our fitness center is open 24/7 and is available for all guests at no extra charge.
    Feel free to use it whenever you like during your stay.
    If you have any other questions or need further assistance, don't hesitate to ask!

    <Example 2>:
    <Human>:
    <Question>:
    How many of them do you have?
    <Information>:
    Yes, we have an indoor swimming pool available for all guests.
    <Memory>:
    Do you have swimming pools?
    Yes, we have an indoor swimming pool available for all guests at no extra charge.
    Feel free to use it whenever you like during your stay.
    If you have any other questions or need further assistance, don't hesitate to ask!
    <AI>:
    We have a single indoor swimming pool.
    Do you have any other questions?

    Now it's your turn:
    """
    prompt = f" System Message: {system_message} <Question>: {question} <Information>: {answer} <Memory>: {memory}"
    print("[DEBUG] Memory: ",memory)

    answer = _ask_llm(user=user, prompt=prompt)

    return answer, memory, system_message, 200

async def _ask_llm(user:User, prompt:str) ->str:
    llm = await _get_llm(model_name=user.llm)
    final_answer = llm.invoke(prompt)
    final_answer = final_answer.content
    return final_answer


async def _get_llm(model_name:str):
    load_dotenv()
    if model_name == "openai":
        OPENAI_KEY = os.getenv("OPENAI_KEY")
        llm = OpenAI(api_key=OPENAI_KEY, model="gpt-3.5-turbo-instruct")
    elif model_name == "azure_openai":
        AZURE_AD_TOKEN = os.getenv("AZURE_AD_TOKEN")
        AZURE_AD_TOKEN_PROVIDER = os.getenv("AZURE_AD_TOKEN_PROVIDER")
        AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
        AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
        llm = AzureOpenAI(azure_ad_token=AZURE_AD_TOKEN, azure_ad_token_provider=AZURE_AD_TOKEN_PROVIDER, azure_deployment=AZURE_DEPLOYMENT, azure_endpoint=AZURE_ENDPOINT, model="gpt-3.5-turbo-instruct")
    elif model_name == "llama3":
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        os.environ["GROQ_API_KEY"] = GROQ_API_KEY
        llm = ChatGroq(api_key=GROQ_API_KEY, model_name="llama3-70b-8192")
    else:
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY,model="gemini-pro")
    return llm


async def _get_vector_file(username: str)-> any:
    with open(username+".pkl", "rb") as f:
        vector_store = pickle.load(f)
    return vector_store


async def _log(user: User, memory:str, question: str, system_message: str, selected_function: str, answer: str, final_answer: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = user.username
    llm = user.llm
    embedder = user.embedder

    log_message = f"\n{timestamp}, Username: {username}, Memory: {memory}, Question: {question}, LLM: {llm}, Embedder: {embedder}, System Message: {system_message}, Selected Function: {selected_function}, Answer: {answer}, Final Answer: {final_answer}\n"
    with open("log.txt", "a", encoding="utf-8") as file:
        file.write("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")
        file.write(log_message)
        file.write("------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------")