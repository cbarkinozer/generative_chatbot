import re
from datetime import datetime

class Booking:
    def __init__(self, full_name:str=None, phone_number:str=None, email:str=None, start_date:str=None, end_date:str=None, guest_count:int=None, room_type:str=None, number_of_rooms:int=None, payment_method:str=None, include_breakfast:bool=None, note:str=None):
        self.full_name = full_name
        self.phone_number = phone_number
        self.email = email
        self.start_date = start_date
        self.end_date = end_date
        self.guest_count = guest_count
        self.room_type = room_type
        self.number_of_rooms = number_of_rooms
        self.payment_method = payment_method
        self.include_breakfast = include_breakfast
        self.note = note if note else {}

    def show_booking_details(self):
        """Returns each field in a formatted string."""
        details = (
            f"Name: {self.full_name}\n"
            f"Phone Number: {self.phone_number}\n"
            f"Email: {self.email}\n"
            f"Start Date: {self.start_date}\n"
            f"End Date: {self.end_date}\n"
            f"Guest Count: {self.guest_count}\n"
            f"Room Type: {self.room_type}\n"
            f"Number of Rooms: {self.number_of_rooms}\n"
            f"Payment Method: {self.payment_method}\n"
            f"Include Breakfast: {self.include_breakfast}\n"
            f"Extra Details: {self.note}\n"
        )
        return details
    
    def get_booking_details(self) -> dict:
        """Returns each field in a dictionary."""
        details = {
            "full_name": self.full_name,
            "phone_number": self.phone_number,
            "email": self.email,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "guest_count": self.guest_count,
            "room_type": self.room_type,
            "number_of_rooms": self.number_of_rooms,
            "payment_method": self.payment_method,
            "include_breakfast": self.include_breakfast,
            "note": self.note
        }
        return details


    def is_valid(self) -> tuple[bool, str]:
        """Checks the validation of the value of the each field."""
        # Date checks
        try:
            start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
        except ValueError:
            return False, "Dates must be in YYYY-MM-DD format. Are you sure you entered the start and end date?"

        if start_date >= end_date:
            return False, "End date must be after start date."
        
        if self.room_type != 'single' and self.room_type != 'double' and self.room_type != 'suite':
            return False, "Room type can be either single, double, or suite."

        # Guest count check
        if self.guest_count <= 0:
            return False, "Guest count must be at least 1."

        # Room count check
        if self.number_of_rooms <= 0:
            return False, "Number of rooms must be at least 1."

        # Phone number check (simple validation for digits only, length may vary by country)
        if not re.match(r"^\d{10,15}$", self.phone_number):
            return False, "Phone number must be between 10 and 15 digits."

        # Email format check
        if not re.match(r"[^@]+@[^@]+\.[^@]+", self.email):
            return False, "Invalid email format. Are you sure you entered email correctly?"

        # Include breakfast check (should be a boolean)
        if not isinstance(self.include_breakfast, bool):
            return False, "Include breakfast must be a boolean."
        return True, "Booking is valid."