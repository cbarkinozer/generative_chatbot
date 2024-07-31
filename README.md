# generative_chatbot
A chatbot that can answer questions and do booking using natural language input.

The user interface is created with streamlit.

# Simple booking dialogues 
Below are the simple booking dialogues that are gathered from internet to test and develop the application better.


# Architecture
* There are 2 pages admin uploads file with his password (password is set at .env file and can be change from the admin-ui after setting it correctly).
* On the user-ui, user will ask questions or can book. Booking or question answering is decided as function calling.
* If question answered is selected: In question answering questions are answered from predetermined questions (a dictionary that can be updated from admin-ui) and a document where RAG (uses path) will be done if no question is matched.
* If booking is selected: question is asked and json filled and checked if all values are set if not asked back. If all values are set one last approve is asked and later save on sql built-in database.

