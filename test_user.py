import unittest
from unittest.mock import patch, MagicMock
from user import User
from booking import Booking
from hotel_manager import HotelManager
from memory import Memory

class TestUser(unittest.TestCase):

    @patch('user.Memory')
    @patch('user.HotelManager')
    def test_user_initialization(self, mock_hotel_manager, mock_memory):
        """Test that User is initialized with correct attributes."""
        # Mock instances for external dependencies
        mock_memory_instance = mock_memory.return_value
        mock_hotel_manager_instance = mock_hotel_manager.return_value

        # Create User instance
        user = User(username="testuser")

        # Assert that the username is set correctly
        self.assertEqual(user.username, "testuser")

        # Assert default LLM and embedder values
        #self.assertEqual(user.llm, "llama3")
        self.assertEqual(user.embedder, "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

        # Assert that memory and hotel management are initialized correctly
        self.assertEqual(user.memory, mock_memory_instance)
        self.assertEqual(user.hotel_management, mock_hotel_manager_instance)

        # Assert that booking and room_id are None by default
        self.assertIsNone(user.booking)
        self.assertIsNone(user.room_id)

    def test_set_and_get_booking(self):
        """Test setting and getting the booking object."""
        # Create User instance
        user = User(username="testuser")

        # Create a mock booking instance
        mock_booking = MagicMock(spec=Booking)

        # Set the booking
        user.set_booking(mock_booking)

        # Assert that the booking is set and retrieved correctly
        self.assertEqual(user.get_booking(), mock_booking)

    def test_set_and_get_room_id(self):
        """Test setting and getting the room_id."""
        # Create User instance
        user = User(username="testuser")

        # Set a room ID
        user.set_room_id(101)

        # Assert that the room ID is set and retrieved correctly
        self.assertEqual(user.get_room_id(), 101)

    def test_set_llm(self):
        """Test setting the LLM model."""
        # Create User instance
        user = User(username="testuser")

        # Set a new LLM model
        user.set_llm("chatgpt")

        # Assert that the LLM model is updated
        self.assertEqual(user.llm, "chatgpt")

    @patch('user.HotelManager')
    def test_get_hotel_management(self, mock_hotel_manager):
        """Test that hotel management is retrieved correctly."""
        # Create mock instance of HotelManager
        mock_hotel_manager_instance = mock_hotel_manager.return_value

        # Create User instance
        user = User(username="testuser")

        # Assert that the hotel management object is retrieved correctly
        self.assertEqual(user.get_hotel_management(), mock_hotel_manager_instance)


if __name__ == '__main__':
    unittest.main()
