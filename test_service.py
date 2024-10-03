import unittest
from unittest.mock import patch, AsyncMock, MagicMock
from service import upload_documents, _extract_text_from_document, _chunk_text, _create_embeddings_and_save
from user import User
from fastapi import UploadFile


class TestService(unittest.IsolatedAsyncioTestCase):

    @patch('service.os.getenv')
    async def test_upload_documents_invalid_password(self, mock_getenv):
        # Mocking environment variable and input
        mock_getenv.return_value = "admin_password"
        user = User(username="test_user")
        files = [UploadFile(filename="test.pdf", file=AsyncMock())]
        password = "wrong_password"

        result = await upload_documents(user, files, password)
        self.assertEqual(result, ("Only ADMIN can insert files.", 400))

    @patch('service.os.getenv')
    @patch('service._extract_text_from_document', return_value="Mocked text")
    @patch('service._chunk_text', return_value=["chunk1", "chunk2"])
    @patch('service._create_embeddings_and_save')
    async def test_upload_documents_success(self, mock_create_embeddings, mock_chunk, mock_extract, mock_getenv):
        # Mocking environment variable and input
        mock_getenv.return_value = "admin_password"
        user = User(username="test_user")
        files = [UploadFile(filename="test.pdf", file=AsyncMock())]
        password = "admin_password"

        result = await upload_documents(user, files, password)

        # Assert that the correct steps are taken
        mock_extract.assert_called_once_with(files)
        mock_chunk.assert_called_once()
        mock_create_embeddings.assert_called_once_with(user, ["chunk1", "chunk2"])

        self.assertEqual(result, ("Document is uploaded successfully.", 200))

    @patch('service.PyPDF2.PdfReader')
    @patch('service.Document')
    async def test_extract_text_from_document_pdf(self, mock_Document, mock_PdfReader):
        # Mock a PDF file read process
        mock_pdf_reader = MagicMock()
        mock_pdf_reader.pages = [MagicMock(extract_text=MagicMock(return_value="page_text"))]
        mock_PdfReader.return_value = mock_pdf_reader

        file = AsyncMock(filename="test.pdf")
        file.read = AsyncMock(return_value=b"mock_bytes")

        result = await _extract_text_from_document([file])
        self.assertEqual(result, "page_text")

    @patch('service.Document')
    async def test_extract_text_from_document_docx(self, mock_Document):
        # Mock a DOCX file read process
        mock_document = MagicMock()
        mock_document.paragraphs = [MagicMock(text="paragraph_text")]
        mock_Document.return_value = mock_document

        file = AsyncMock(filename="test.docx")
        file.read = AsyncMock(return_value=b"mock_bytes")

        result = await _extract_text_from_document([file])
        self.assertEqual(result, "paragraph_text\n")

    async def test_chunk_text(self):
        # Test for the _chunk_text function
        text = "This is a sample text that will be chunked into smaller parts."
        chunks = await _chunk_text(text)
        self.assertIsInstance(chunks, list)
        self.assertGreater(len(chunks), 0)

    @patch('service.FAISS')
    @patch('service.pickle')
    async def test_create_embeddings_and_save(self, mock_pickle, mock_FAISS):
        # Mock embeddings and FAISS save
        mock_faiss = MagicMock()
        mock_FAISS.from_texts.return_value = mock_faiss

        user = User(username="test_user")
        chunks = ["chunk1", "chunk2"]
        
        result = await _create_embeddings_and_save(user, chunks)
        
        mock_FAISS.from_texts.assert_called_once()
        mock_pickle.dump.assert_called_once()
        self.assertEqual(result, mock_faiss)


if __name__ == '__main__':
    unittest.main()
