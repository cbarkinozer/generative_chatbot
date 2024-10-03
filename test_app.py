import unittest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from app import app

# Create a TestClient instance
client = TestClient(app)

class TestApp(unittest.TestCase):

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"success": "true"})

    @patch('app.upload_documents', new_callable=AsyncMock)
    def test_document_uploader(self, mock_upload_documents):
        """Test document uploader endpoint"""
        # Mock the response from upload_documents
        mock_upload_documents.return_value = ("Document uploaded successfully", 200)

        # Simulate a request with files and form data
        files = [('files', ('testfile.txt', b'file content'))]
        response = client.post("/document-uploader", files=files, data={"password": "password"})

        # Check the status code and response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"response": "Document uploaded successfully"})

    @patch('app.ask_question', new_callable=AsyncMock)
    def test_question_answerer(self, mock_ask_question):
        """Test question answerer endpoint"""
        # Mock the response from ask_question
        mock_ask_question.return_value = ("Answer to the question", 200)

        # Simulate a request with form data
        response = client.post("/question-answerer", data={"username": "testuser", "question": "What is FastAPI?"})

        # Check the status code and response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"response": "Answer to the question"})

    @patch('app.upload_documents', new_callable=AsyncMock)
    def test_document_uploader_fail(self, mock_upload_documents):
        """Test document uploader endpoint with failure"""
        # Mock the failure response from upload_documents
        mock_upload_documents.return_value = ("Invalid password", 400)

        # Simulate a request with files and wrong password
        files = [('files', ('testfile.txt', b'file content'))]
        response = client.post("/document-uploader", files=files, data={"password": "wrong_password"})

        # Check the status code and response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"response": "Invalid password"})

    @patch('app.ask_question', new_callable=AsyncMock)
    def test_question_answerer_fail(self, mock_ask_question):
        """Test question answerer endpoint with failure"""
        # Mock the failure response from ask_question
        mock_ask_question.return_value = ("Unauthorized user", 403)

        # Simulate a request with invalid user
        response = client.post("/question-answerer", data={"username": "invalid_user", "question": "What is FastAPI?"})

        # Check the status code and that an exception is raised
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json(), {"detail": "Unauthorized user"})

if __name__ == '__main__':
    unittest.main()
