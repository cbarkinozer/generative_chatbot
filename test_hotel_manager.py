import unittest
from unittest.mock import patch, MagicMock
from hotel_manager import HotelManager
import json

class TestHotelManager(unittest.TestCase):
    def setUp(self):
        # Mock sqlite3 connection and cursor
        self.patcher = patch('sqlite3.connect')
        self.mock_connect = self.patcher.start()
        self.mock_conn = MagicMock()
        self.mock_connect.return_value = self.mock_conn
        self.mock_cursor = MagicMock()
        self.mock_conn.cursor.return_value = self.mock_cursor

        # Initialize HotelManager instance
        self.hotel_manager = HotelManager(db_name=":memory:")

    def tearDown(self):
        # Stop the patcher to clean up after tests
        self.patcher.stop()

    def test_reserve_room_no_availability(self):
        # Mock no available rooms
        self.mock_cursor.fetchone.return_value = None  # No available rooms
        
        room_id, msg = self.hotel_manager.reserve_room(
            full_name="Test User",
            phone_number="5555555555",
            email="test@example.com",
            room_type="single",
            start_date="2024-10-03",
            end_date="2024-10-07",
            guest_count=1,
            number_of_rooms=1,
            payment_method="credit card",
            include_breakfast=True,
            note="Test reservation."
        )

        self.assertIsNone(room_id)
        self.assertIn("No available rooms", msg)

    def test_cancel_reservation(self):
        # Mock a valid reservation to cancel
        self.mock_cursor.fetchone.return_value = [1]  # Assume reservation_id 1 exists
        
        cancel_msg = self.hotel_manager.cancel_reservation(room_id=101)
        
        self.assertIn("canceled", cancel_msg)
        
        # Check if reservation was deleted
        self.mock_cursor.execute.assert_any_call('''DELETE FROM reservation_rooms WHERE room_id = ?''', (101,))
        self.mock_cursor.execute.assert_any_call('''DELETE FROM reservations WHERE reservation_id = ?''', (1,))
        
        # Check if room was marked available
        self.mock_cursor.execute.assert_any_call('''UPDATE rooms SET is_available = 1 WHERE room_id = ?''', (101,))

    def test_invalid_date_format(self):
        # Test invalid date format during reservation
        room_id, msg = self.hotel_manager.reserve_room(
            full_name="Test User",
            phone_number="5555555555",
            email="test@example.com",
            room_type="single",
            start_date="03-10-2024",  # Invalid date format
            end_date="07-10-2024",    # Invalid date format
            guest_count=1,
            number_of_rooms=1,
            payment_method="credit card",
            include_breakfast=True,
            note="Test reservation."
        )
        self.assertIsNone(room_id)
        self.assertIn("Invalid date format", msg)

if __name__ == '__main__':
    unittest.main()
