# generative_chatbot
A chatbot that can answer questions and do booking using natural language input.

UI is gradio because it is easy to integrate in a website.
Single page dummy fasthtml website will created and gradio project will be integrated.

For small model requests (the error message format, not main operations), it is possible to use Ollama and phi-3.5 to run on CPU but for ease free API request to Groq is preffered.
Also it can increase latency and might not do function calling.

create the room state and reservation system and connect them with llm

# Simple booking dialogues 
Simple booking dialogues that are used can be found in document.txt.  
LLMs are utilized to generate example question answer pairs to do Retrieval Augmented Generation.  
Application is tested with a real user, the questions the user asked is added to the RAG document.  

# Architecture
* There are 2 pages admin uploads file with his password (password is set at .env file and can be change from the admin-ui after setting it correctly).
* On the user-ui, user will ask questions or can book. Booking or question answering is decided as function calling.
* If question answered is selected: In question answering questions are answered from given document.
* If booking is selected: question is asked and json filled and checked if all values are set if not asked back. If all values are set one last approve is asked and later save on sql built-in database.


# Testing and improving
* Add smaller llm requests for warning messages
* real user testing with efe and Bülent abi