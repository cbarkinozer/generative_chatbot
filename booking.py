import re
import datetime

class Booking:
    def __init__(self, full_name:str, phone_number:str, email:str, start_date:str, end_date:str, guest_count:int, room_type:str, number_of_rooms:int, payment_method:str, include_breakfast:bool, extra_details:str=None):
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
        self.extra_details = extra_details if extra_details else {}

    def display_booking_details(self):
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
            f"Extra Details: {self.extra_details}"
        )
        return details

    def is_valid(self):
        
        none_fields = []
        for field_name, value in self.__dict__.items():
            if value is None:
                none_fields.append(field_name)
        
        if none_fields:
            message = f"The following fields are could not found: {', '.join(none_fields)}"
            return False, message
        
        # Date checks
        try:
            start_date = datetime.strptime(self.start_date, "%Y-%m-%d")
            end_date = datetime.strptime(self.end_date, "%Y-%m-%d")
        except ValueError:
            return False, "Dates must be in YYYY-MM-DD format."

        if start_date >= end_date:
            return False, "End date must be after start date."

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
            return False, "Invalid email format."

        # Include breakfast check (should be a boolean)
        if not isinstance(self.include_breakfast, bool):
            return False, "Include breakfast must be a boolean."

        return True, "Booking is valid."