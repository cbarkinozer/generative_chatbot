import gradio as gr
import requests
import os
from dotenv import load_dotenv
import random
import string

load_dotenv('.env')
API_URL = os.getenv("API_URL")

class PDFChatBot:
    def __init__(self):
        self.username = "ADMIN"

    def render_file(self, files, password):
        files_dict = {}

        # Check if files is a list or a single file
        if isinstance(files, list):
            for i, file in enumerate(files):
                if hasattr(file, 'read'):  # Check if it's a file-like object
                    files_dict[f"files[{i}]"] = (file.name, file, 'application/octet-stream')
                else:
                    # Handle file paths or other types if necessary
                    files_dict[f"files[{i}]"] = (f"file_{i}.txt", open(file, 'rb'), 'application/octet-stream')
        else:
            if hasattr(files, 'read'):  # If only one file is uploaded
                files_dict["files"] = (files.name, files, 'application/octet-stream')
            else:
                files_dict["files"] = (f"file_0.txt", open(files, 'rb'), 'application/octet-stream')

        # Send the POST request with the files and password
        response = requests.post(f"{API_URL}/document-uploader", files=files_dict, data={"password": password})

        # Handle the response
        if response.status_code == 200:
            return gr.update(visible=True, value="Document uploaded successfully!")
        else:
            return gr.update(visible=True, value=f"Error: {response.status_code} - {response.text}")

    def add_text(self, chat_history, text):
        # Ensure chat_history is a list of lists
        if chat_history is None:
            chat_history = []

        chat_history.append([text, ""])  # user message, assistant response placeholder
        return chat_history

    def generate_response(self, chat_history, text):
        characters = string.ascii_letters + string.digits
        username = ''.join(random.choice(characters) for _ in range(6))

        response = requests.post(f"{API_URL}/question-answerer", data={"username": username, "question": text})

        if response.status_code == 200:
            try:
                assistant_message = response.json()  # Ensure the API returns JSON
                if isinstance(assistant_message, dict):  # Check if the response is a dictionary
                    assistant_message = assistant_message.get('response', '')

                if chat_history:
                    chat_history[-1][1] = assistant_message  # Update the assistant's response
                else:
                    chat_history.append(["", assistant_message])  # Add a new entry if `chat_history` was empty
            except ValueError as e:
                # Handle cases where the response is not JSON
                chat_history[-1][1] = f"Error: Couldn't decode JSON. {str(e)}"
        else:
            error_message = response.text
            if chat_history:
                chat_history[-1][1] = error_message
            else:
                chat_history.append(["", error_message])  # Handle empty `chat_history`

        return chat_history, ""  # Returning an empty string to reset the text input

# Gradio application setup
def create_demo():
    with gr.Blocks(title="Hotel Booking Chatbot") as demo:
        with gr.Row():
            chat_history = gr.Chatbot(
                label='Hotel Chatbot',
                value=[["**enters**", "Hi! 😊 You are welcome to ask me any questions about the hotel or to book.\n If you want to book, I will require at least the following information:\n Full name, phone number, email address, booking start and finish dates, guest count, room type, number of rooms, payment method, breakfast."]],
                elem_id='chatbot',
                height=680
            )
        
        with gr.Row():
            with gr.Column(scale=5):
                text_input = gr.Textbox(
                    show_label=False,
                    placeholder="Type your question here...",
                    container=False
                )

            with gr.Column(scale=1):
                submit_button = gr.Button('Send')

        return demo, chat_history, text_input, submit_button

def create_admin_interface():
    with gr.Blocks(title="Admin's Document Uploading Page") as app1:

        with gr.Row():
            with gr.Column(scale=2):
                password = gr.Textbox(
                    show_label=False,
                    placeholder="Admin password to upload document.",
                    container=False,
                )

            with gr.Column(scale=2):
                uploaded_pdf = gr.UploadButton("📁 Upload Document", file_types=[".txt,.pdf,.docx"])
        
        # Hidden component to show success/failure messages
        upload_status = gr.Textbox(visible=False, label="Upload Status")

        return app1, uploaded_pdf, upload_status, password

# Create Gradio interfaces
demo, chat_history, text_input, submit_button = create_demo()
app1, uploaded_pdf, upload_status, password = create_admin_interface()

pdf_chatbot = PDFChatBot()

with demo:
    # Event handler for submitting text and generating response
    submit_button.click(
        pdf_chatbot.add_text, 
        inputs=[chat_history, text_input], 
        outputs=[chat_history]
    ).success(
        pdf_chatbot.generate_response, 
        inputs=[chat_history, text_input], 
        outputs=[chat_history, text_input],
    )

with app1:
    # Event handler for uploading a PDF
    uploaded_pdf.upload(pdf_chatbot.render_file, inputs=[uploaded_pdf, password], outputs=[upload_status])

if __name__ == "__main__":
    # Combine the chatbot interface with other tabs
    main_demo = gr.TabbedInterface([demo, app1], ["Chatbot", "Document Uploading"])
    main_demo.launch()
