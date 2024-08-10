import gradio as gr
import requests
import os
from dotenv import load_dotenv

load_dotenv('.env')
API_URL = os.getenv("API_URL")

class PDFChatBot:
    def __init__(self):
        self.username = "ADMIN"

    def render_file(self, files, password):
        # Prepare the files for the request
        files_dict = {}
        for i, file in enumerate(files):
            files_dict[f"file_{i}"] = (file.name, file, file.type)
        
        # Send the POST request with the files and password
        response = requests.post(f"{API_URL}/document-uploader", files=files_dict, data={"password": password})
        
        # Handle the response
        if response.status_code == 200:
            return gr.update(visible=True, value="Document uploaded successfully!")
        else:
            return gr.update(visible=True, value=f"Error: {response.status_code} - {response.text}")

    def add_text(self, chat_history, text):
        chat_history.append({"role": "user", "content": text})
        return chat_history

    def generate_response(self, chat_history, text, uploaded_pdf):
        response = requests.post(f"{API_URL}/question-answerer", data={"username": self.username, "question": text})
        if response.status_code == 200:
            assistant_message = response.json()  # Adjust this based on actual response structure
            chat_history.append({"role": "assistant", "content": assistant_message})
        else:
            chat_history.append({"role": "assistant", "content": f"Error: {response.status_code} - {response.text}"})
        return chat_history, ""

# Gradio application setup
def create_demo():
    with gr.Blocks(title="Hotel Booking Chatbot", theme="Soft") as demo:
        with gr.Row():
            chat_history = gr.Chatbot(label='Hotel Chatbot', value=[["", "Hi! 😊 You can ask me a question about the hotel or you can book.\n I need at least these information if you want to book: full name, phone number, email, booking start date, booking end date, guest count, room type, number of rooms, payment method, breakfast."]], elem_id='chatbot', height=680)
        
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
    with gr.Blocks(title="Admin's Document Uploading Page", theme="Soft") as app1:
        with gr.Row():
            chat_history = gr.Chatbot(label='response', value=[], elem_id='response', height=100)

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

# Create PDFChatBot instance
pdf_chatbot = PDFChatBot()

# Set up event handlers
with demo:
    # Event handler for submitting text and generating response
    submit_button.click(
        pdf_chatbot.add_text, 
        inputs=[chat_history, text_input], 
        outputs=[chat_history], 
        queue=False
    ).success(
        pdf_chatbot.generate_response, 
        inputs=[chat_history, text_input, uploaded_pdf], 
        outputs=[chat_history, text_input]
    )

with app1:
    # Event handler for uploading a PDF
    uploaded_pdf.upload(pdf_chatbot.render_file, inputs=[uploaded_pdf, password], outputs=[upload_status])

if __name__ == "__main__":
    # Combine the chatbot interface with other tabs
    main_demo = gr.TabbedInterface([demo, app1], ["Chatbot", "Document Uploading"])
    main_demo.launch()
