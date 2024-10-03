import unittest
from booking import Booking

class TestBooking(unittest.TestCase):

    def setUp(self):
        """Set up a valid booking instance."""
        self.booking = Booking(
            full_name="John Doe",
            phone_number="1234567890",
            email="john.doe@example.com",
            start_date="2024-10-10",
            end_date="2024-10-12",
            guest_count=2,
            room_type="double",
            number_of_rooms=1,
            payment_method="credit_card",
            include_breakfast=True,
            note="Vegetarian meal."
        )

    def test_initialization(self):
        """Test if the booking is initialized with correct values."""
        self.assertEqual(self.booking.full_name, "John Doe")
        self.assertEqual(self.booking.phone_number, "1234567890")
        self.assertEqual(self.booking.email, "john.doe@example.com")
        self.assertEqual(self.booking.start_date, "2024-10-10")
        self.assertEqual(self.booking.end_date, "2024-10-12")
        self.assertEqual(self.booking.guest_count, 2)
        self.assertEqual(self.booking.room_type, "double")
        self.assertEqual(self.booking.number_of_rooms, 1)
        self.assertEqual(self.booking.payment_method, "credit_card")
        self.assertTrue(self.booking.include_breakfast)
        self.assertEqual(self.booking.note, "Vegetarian meal.")

    def test_show_booking_details(self):
        """Test the formatted output of booking details."""
        expected_details = (
            "Name: John Doe\n"
            "Phone Number: 1234567890\n"
            "Email: john.doe@example.com\n"
            "Start Date: 2024-10-10\n"
            "End Date: 2024-10-12\n"
            "Guest Count: 2\n"
            "Room Type: double\n"
            "Number of Rooms: 1\n"
            "Payment Method: credit_card\n"
            "Include Breakfast: True\n"
            "Extra Details: Vegetarian meal.\n"
        )
        self.assertEqual(self.booking.show_booking_details(), expected_details)

    def test_get_booking_details(self):
        """Test the dictionary output of booking details."""
        expected_details = {
            "full_name": "John Doe",
            "phone_number": "1234567890",
            "email": "john.doe@example.com",
            "start_date": "2024-10-10",
            "end_date": "2024-10-12",
            "guest_count": 2,
            "room_type": "double",
            "number_of_rooms": 1,
            "payment_method": "credit_card",
            "include_breakfast": True,
            "note": "Vegetarian meal."
        }
        self.assertEqual(self.booking.get_booking_details(), expected_details)

    def test_is_valid_success(self):
        """Test if valid booking passes all validation checks."""
        is_valid, message = self.booking.is_valid()
        self.assertTrue(is_valid)
        self.assertEqual(message, "Booking is valid.")

    def test_invalid_dates_format(self):
        """Test invalid date format."""
        self.booking.start_date = "10-10-2024"
        self.booking.end_date = "12-10-2024"
        is_valid, message = self.booking.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "Dates must be in YYYY-MM-DD format. Are you sure you entered the start and end date?")

    def test_invalid_dates_order(self):
        """Test if end date is before or same as start date."""
        self.booking.start_date = "2024-10-12"
        self.booking.end_date = "2024-10-10"
        is_valid, message = self.booking.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "End date must be after start date.")

    def test_invalid_room_type(self):
        """Test invalid room type."""
        self.booking.room_type = "luxury"
        is_valid, message = self.booking.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "Room type can be either single, double, or suite.")

    def test_invalid_guest_count(self):
        """Test guest count less than or equal to 0."""
        self.booking.guest_count = 0
        is_valid, message = self.booking.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "Guest count must be at least 1.")

    def test_invalid_number_of_rooms(self):
        """Test number of rooms less than or equal to 0."""
        self.booking.number_of_rooms = 0
        is_valid, message = self.booking.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "Number of rooms must be at least 1.")

    def test_invalid_phone_number(self):
        """Test invalid phone number (non-numeric or wrong length)."""
        self.booking.phone_number = "12345abc"
        is_valid, message = self.booking.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "Phone number must be between 10 and 15 digits.")

    def test_invalid_email_format(self):
        """Test invalid email format."""
        self.booking.email = "johndoe.com"
        is_valid, message = self.booking.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "The email format is invalid, can you check the format?")

    def test_invalid_include_breakfast(self):
        """Test invalid include_breakfast (non-boolean)."""
        self.booking.include_breakfast = "yes"
        is_valid, message = self.booking.is_valid()
        self.assertFalse(is_valid)
        self.assertEqual(message, "Include breakfast must be a boolean.")

if __name__ == '__main__':
    unittest.main()
