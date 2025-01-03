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
import json
from booking import Booking
import sqlite3
from langdetect import detect

USER_STORE = {}

async def upload_documents(user: User, files: list[UploadFile], password:str) -> tuple[str, int]:
    """Checking the password, extracting texts, chunking and creating embeddings from them."""
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
    if password != ADMIN_PASSWORD:
        return "Only ADMIN can insert files.", 400
    text = await _extract_text_from_document(files)
    chunks = await _chunk_text(text)
    await _create_embeddings_and_save(user, chunks)
    return "Document is uploaded successfully.", 200


async def _extract_text_from_document(files: list[UploadFile]) -> str:
    """Extracting text from documents."""
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
    """Splitting text to chunks to get better semantic matches."""
    chunks = None
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=20,
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    return chunks


async def _create_embeddings_and_save(user: User, chunks: any) -> FAISS:
    """An embedding model is running on CPU to create embeddings and save to local"""
    embeddings = HuggingFaceEmbeddings(model_name=user.embedder)
    pkl_name = os.path.join("document.pkl")
    vector_store = FAISS.from_texts(chunks, embeddings, metadatas=[{"source": f"{pkl_name}:{i}"} for i in range(len(chunks))])
    with open(pkl_name, "wb") as f:
        pickle.dump(vector_store, f)
    return vector_store


async def ask_question(user: User, question: str) -> tuple[str, int]: 
    """Customer's inquiry is answered. First user object is retrieved from unique username. Language preference is set if None. Inquirys type is decided using an LLM call."""
    user = await _get_saved_user(user)
    if user.get_language_preference() == None:
        user.set_language_preference(language_preference=detect(question))
    system_message = f"""
        Your task is to classify customer inquiries related to booking or reservation.
        Based on the content of the inquiry, provide the appropriate response from the following options:

        If the customer wants to learn free roms or status of the rooms, respond with "status".
        If the customer explicitly wants to book or reserve, respond with "booking".
        If the customer wants to cancel a booking or reservation, respond with "cancel".
        If the customer is still undecided and is asking questions or gathering information, respond with "question".
        
        Important Notes:
        Booking or reservation inquiries include details about the customer's stay, such as dates, accommodation type, payment methods, or additional services.
        Your responses should only include one word from the options: "booking", "cancel", or "question".
        
        Examples:
        Example 1:
        <Human>:
        Hello, My name is Arda Yılmaz. You can reach me at 123-456-7890 or via email at arda.yilmaz@example.com. We plan to arrive on September 10, 2024, between 1:00 PM and 3:00 PM, and depart on September 20, 2024. My wife and I will be staying in an economy room. I intend to pay with a MasterCard. We would also like to include breakfasts with our stay. Additionally, could you please add access to the spa to our gym plan? Thanks.
        <AI>:
        booking

        Example 2:
        <Human>:
        Hey, I am Barkın Özer. I am planning a vacation in Antalya on August 5, 2024. I wanted to know first, can I book a conference room? Because if we decide to book your hotel, I need a place to do meetings. Thanks.
        <AI>:
        question

        Example 3:
        <Human>:
        I want breakfast. burak@gmail.com. credit card. Burak Çivit.
        <AI>:
        booking

        Example 4:
        <Human>:
        yes sorry, it is barorkar@gmail.com
        <AI>:
        booking

        Example 5:
        <Human>:
        Do you have a room for three people?
        <AI>:
        status

        Example 6:
        <Human>:
        I changed my mind. Please cancel my booking/reservation.
        <AI>:
        cancel

        Now it's your turn:
    """
    prompt = f" System Message: {system_message} <Inquiry>: {question}"
    selected_function = await _ask_llm(user=user,prompt=prompt)
    
    if "booking" in selected_function.lower():
        final_answer, memory, system_message, http_code = await _book(user, question)
    if "status" in selected_function.lower():
        final_answer, memory, system_message, http_code = await _status(user, question)
    if "cancel" in selected_function.lower():
        final_answer, memory, system_message, http_code = await _cancel(user, question)
    elif "question" in selected_function.lower():
        final_answer, memory, system_message, http_code = await _rag(user, question)
    else:
        "Can you explain your request in a different way with more details? I could not understand.", memory, system_message, 400

    print(f"[DEBUG] Selected Function: {selected_function}")
    
    user.memory.save(question=question, answer=final_answer)
    await _log(user=user, memory=memory, question=question, selected_function= selected_function, final_answer = final_answer)
    return final_answer, http_code

async def _status(user:User, question:str)-> tuple[str,str,str,int]:
    """Retrieve room availability status and return to the user."""
    answer = user.get_hotel_management().get_room_status()
    memory = user.memory.get_last_answer()
    language = user.get_language_preference()
    FLUENCY_PROMPT = f"""
        As a realtime chatbot you are texting with the user.
        Your objective is to answer the user's inquiry with the specified answer in a friendly, concise, clear tone.
        Do not greet the user or feel sorry.
        Answer ONLY in the {language} language in which the question was posed.

        Now it's your turn, answer the question in the {language} language with the given answer:
    """
    prompt = f"""{FLUENCY_PROMPT} <chat_memory>: {memory} <question>:{question} <answer>: {answer}"""
    final_answer = await _ask_llm(user=user,prompt=prompt,llm="llama3-small")
    return final_answer, memory, prompt, 200

async def _cancel(user:User, question:str) -> tuple[str,str,str,int]:
    """Cancel reservation if the user have one."""
    room_id = user.get_room_id()
    user.get_hotel_management().cancel_reservation(room_id)
    memory = user.memory.get_last_answer()
    if room_id:
        answer = f"Your reservation is cancelled for the room with the room id: {room_id}"
    else:
        answer = "I can't see a reservation on your account"
    language = user.get_language_preference()
    FLUENCY_PROMPT = f"""
        As a realtime chatbot you are texting with the user.
        Your objective is to answer the user's inquiry with the specified answer in a friendly, concise, clear tone.
        Do not greet the user or feel sorry.
        Answer ONLY in the {language} language in which the question was posed.
        ONLY answer the question do NOT answer <chat_memory>.
    """
    prompt = f"""{FLUENCY_PROMPT} <chat_memory>: {memory} <question>:{question} <answer>: {answer}"""
    final_answer = await _ask_llm(user=user,prompt=prompt,llm="llama3-small")
    return final_answer, memory, prompt, 200


async def _book(user: User, question: str):
    """Get required information in JSON and later book the user."""
    language = user.get_language_preference()
    FLUENCY_PROMPT = f"""
        As a realtime chatbot you are texting with the user.
        Your objective is to answer the user's inquiry with the specified answer in a friendly, concise, clear tone.
        Do not greet the user or feel sorry.
        Answer ONLY in the {language} language in which the question was posed.
        ONLY answer the question do NOT answer <chat_memory>.
    """

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
    note: (Optional) other informations

    Do NOT forget:
    Room type only can be single (for 1-2 people) double (for 3-4 people) or suite (for 4-5 people).
    Dates must be in YYYY-MM-DD format.
    End date must be after start date.
    Guest count must be at least 1.
    Number of rooms must be at least 1.
    Phone number must be between 10 and 15 digits.
    Include breakfast must be a boolean.

    If you can not find the value just leave that field empty like this: ""

    <Example>
    <Human>:
    Hi, I am Barkın Özer. You can call me from 5365363636 or mail me at c.barkinozer@gmail.com, We plan to be there at 15 August 2024 between 00.00 pm to 02.00 pm and leave at the 24 th.
    Me and my girlfriend will stay on an economy room. I am planning to pay with visa card. We want breakfasts as well. Please include that.
    Also can you add spa to our gym plan as well? Thanks.

    <AI>:
    {
        "full_name": "Barkın Özer",
        "phone_number": "5365363636",
        "email": "c.barkinozer@gmail.com",
        "start_date": "2024-08-15",
        "end_date": "2024-08-24",
        "guest_count": 2,
        "room_type": "single",
        "number_of_rooms": 1,
        "payment_method": "credit card",
        "include_breakfast": true,
        "note": "Visa card will be used as credit card. Spa will be added to the gym plan. Planning to arrive between 00.00 pm to 02.00 pm."
    }

    Now it's your turn:
    """
    memory = user.memory.get_memory()
    date = f"Current date (Year-Month-Date Hour-Minute-Second): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    prompt = f" System Message: {system_message} <Question>: {question} <Memory>: {memory}, <Date>: {date}"
    print("[DEBUG] Memory: ", memory)
    
    json_string = await _ask_llm(user=user, prompt=prompt)
    
    try:
        data = json.loads(json_string)
    except Exception as e:
        # Booking request with no info is given
        print(f"An exception has occured: {e}\n")
        print(json_string)
        memory = user.memory.get_last_answer()
        prompt = f"""{FLUENCY_PROMPT} <chat_memory>: {memory} <question>:{question} <answer>:For me to book you, please tell me your full name, phone number, email, booking start date, booking end date, guest count, room type (single (1-2 people), double (3-4 people), suite (4-5 people), number of rooms, payment method. Also do you want breakfasts?"""
        final_answer = await _ask_llm(user=user,prompt=prompt,llm="llama3-small")
        return final_answer, memory, prompt, 200

    print(data)
    
    # Check for each key and assign if it exists
    full_name = data['full_name'] if 'full_name' in data else None
    phone_number = data['phone_number'] if 'phone_number' in data else None
    email = data['email'] if 'email' in data else None
    start_date = data['start_date'] if 'start_date' in data else None
    end_date = data['end_date'] if 'end_date' in data else None
    guest_count = data['guest_count'] if 'guest_count' in data else None
    room_type = data['room_type'] if 'room_type' in data else None
    number_of_rooms = data['number_of_rooms'] if 'number_of_rooms' in data else None
    payment_method = data['payment_method'] if 'payment_method' in data else None
    include_breakfast = data['include_breakfast'] if 'include_breakfast' in data else None
    note = data['note'] if 'note' in data else None

    scrapped_data = {
        "full_name":full_name,
        "phone_number":phone_number,
        "email": email,
        "start_date":start_date,
        "end_date":end_date,
        "guest_count":guest_count,
        "room_type":room_type,
        "number_of_rooms":number_of_rooms,
        "payment_method": payment_method,
        "include_breakfast": include_breakfast,
        "note": note
    }

    none_fields = []
    booking = user.get_booking()

    if booking is None:
        booking = Booking()

    for field_name, value in scrapped_data.items():
        if (value == "" or value is None) and (field_name != "note" and getattr(booking, field_name) is None):
            field_name = field_name.replace("_", " ")
            none_fields.append(field_name)
        else:
            setattr(booking, field_name, value)

    user.set_booking(booking=booking)
    
    if none_fields:
        memory = user.memory.get_last_answer()
        prompt = f"""{FLUENCY_PROMPT} <chat_memory>: {memory} <question>:{question} <answer>: You need to tell me these information as well please: {', '.join(none_fields)}"""
        final_answer = await _ask_llm(user=user,prompt=prompt,llm="llama3-small")
        return final_answer, memory, prompt, 200
    
    is_valid, message = booking.is_valid()
    
    if not is_valid:
        memory = user.memory.get_last_answer()
        prompt = f"""{FLUENCY_PROMPT} <chat_memory>: {memory} <question>:{question} <answer>: {message}"""
        final_answer = await _ask_llm(user=user,prompt=prompt,llm="llama3-small")
        return final_answer, memory, prompt, 400
    
    details = user.booking.get_booking_details()
    room_id, reservation_response = user.get_hotel_management().reserve_room(full_name=details["full_name"], phone_number=details["phone_number"], email=details["email"], room_type=details["room_type"],
                                             start_date=details["start_date"],end_date=details["end_date"],guest_count=details["guest_count"],number_of_rooms=details["number_of_rooms"],
                                             payment_method=details["payment_method"],include_breakfast=details["include_breakfast"],note=details["note"])
    user.set_room_id(room_id=room_id)
    memory = user.memory.get_last_answer()
    prompt = f"""{FLUENCY_PROMPT} <chat_memory>: {memory} <question>:{question} <answer>: Great 😊 {reservation_response}\n Details: {details}"""
    final_answer = await _ask_llm(user=user,prompt=prompt,llm="llama3-small")
    final_answer += f"\n [DEBUG]: Booking is saved successfully: {details}"
    return final_answer, memory, system_message, 200


async def _get_saved_user(user: User) -> User:
    """User is retrieved from user store according to the unique username."""
    if user.username in USER_STORE:
        return USER_STORE[user.username]
    else:
        USER_STORE[user.username] = user
        return user


async def _rag(user: User, question: str):
    """Similar answer is retrieved from the FAQ document."""
    vector_store = await _get_vector_file()
    if vector_store is None:
        return "Document not found.", None, None, 400
    
    llm = await _get_llm(model_name=user.llm)
    memory = user.memory.get_memory()
    docs = vector_store.similarity_search(question+memory)
    retrieved_chunks = docs[0].page_content + docs[1].page_content + docs[2].page_content
    language = user.get_language_preference
    system_message= f"Figure out the answer of the question by the given information pieces. ALWAYS answer in {language} language."
    prompt = system_message + "Question: " + question + " Context: " + retrieved_chunks
    try:
        response = llm.invoke(prompt)
    except Exception as e:
        return f"LLM call error: {e}", None, None, 400
    answer = response.content
    print(f"[DEBUG] RAG Results: {answer}")

    system_message = f"""
    You are a reservation assistant who books and reserves places.
    Your task is to answer the questions asked by the user using the information provided to you.
    The tone of your answers is friendly and neutral.
    Your response should be at least a few sentences long.
    NEVER use information outside of what is provided to you.
    Answer ONLY in the {language} language in which the question was posed.
    Your answer will be directly send to the user so do not say something like "here is my response:"

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
    <Date>:
    Current date (Year-Month-Date Hour-Minute-Second): 2024-08-17 20:09:44.988306

    <AI>:
    We have a single indoor swimming pool.
    Do you have any other questions?

    Now it's your turn, answer ONLY in the {language} language:
    """
    date = f"Current date (Year-Month-Date Hour-Minute-Second): {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    prompt = f" System Message: {system_message} <Question>: {question} <Information>: {answer} <Memory>: {memory}, <Date>: {date}"
    print("[DEBUG] Memory: ",memory)

    answer = await _ask_llm(user=user, prompt=prompt)
    return answer, memory, system_message, 200

async def _ask_llm(user:User, prompt:str, llm:str=None) ->str:
    """LLM call."""
    if llm:
        model_name = llm
    else:
        model_name = user.llm
    llm = await _get_llm(model_name=model_name)
    final_answer = llm.invoke(prompt)
    final_answer = final_answer.content
    return final_answer


async def _get_llm(model_name:str):
    """LLM adapter using langchain wrappers."""
    is_loaded = load_dotenv('.env')
    print(f"[DEBUG] Is .env loaded: {is_loaded}")
    if model_name == "openai":
        OPENAI_KEY = os.getenv("OPENAI_KEY")
        llm = OpenAI(api_key=OPENAI_KEY, model="gpt-3.5-turbo-instruct", temperature=0)
    elif model_name == "azure_openai":
        AZURE_AD_TOKEN = os.getenv("AZURE_AD_TOKEN")
        AZURE_AD_TOKEN_PROVIDER = os.getenv("AZURE_AD_TOKEN_PROVIDER")
        AZURE_DEPLOYMENT = os.getenv("AZURE_DEPLOYMENT")
        AZURE_ENDPOINT = os.getenv("AZURE_ENDPOINT")
        llm = AzureOpenAI(azure_ad_token=AZURE_AD_TOKEN, azure_ad_token_provider=AZURE_AD_TOKEN_PROVIDER, azure_deployment=AZURE_DEPLOYMENT, azure_endpoint=AZURE_ENDPOINT, model="gpt-3.5-turbo-instruct", temperature=0)
    elif model_name == "llama3":
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        llm = ChatGroq(api_key=GROQ_API_KEY, model_name="llama3-70b-8192", temperature=0)
    elif model_name == "llama3-small":
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        llm = ChatGroq(api_key=GROQ_API_KEY, model_name="llama3-8b-8192", temperature=0)
    elif model_name == "gemma2-2b":
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY,model="gemma-2-2b-it", temperature=0)
    else:
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        llm = ChatGoogleGenerativeAI(google_api_key=GOOGLE_API_KEY,model="gemini-pro", temperature=0)
    return llm


async def _get_vector_file()-> any:
    with open("document.pkl", "rb") as f:
        vector_store = pickle.load(f)
    return vector_store


async def _log(user: User, memory: str, question: str, selected_function: str, final_answer: str) -> None:
    """Create or connect to an SQLite database and ensure table exists."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    username = user.username
    llm = user.llm
    embedder = user.embedder

    # Connect to the SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("log_data.db")
    cursor = conn.cursor()

    # Create the logs table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            username TEXT,
            memory TEXT,
            question TEXT,
            llm TEXT,
            embedder TEXT,
            selected_function TEXT,
            final_answer TEXT
        )
    ''')

    # Insert log data
    cursor.execute('''
        INSERT INTO logs (timestamp, username, memory, question, llm, embedder, selected_function, final_answer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (timestamp, username, memory, question, llm, embedder, selected_function, final_answer))

    # Commit the transaction and close the connection
    conn.commit()
    conn.close()
