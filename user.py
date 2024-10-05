from memory import Memory
from booking import Booking
from hotel_manager import HotelManager

class User:
    def __init__(self, username):
        # Each user has a username, llm preference, embedding model preference, memory, hotel management, booking details and room id that it's booked.
        self.username = username
        self.llm = "llama3" #gemini-pro
        self.embedder = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.memory = Memory()
        self.hotel_management = HotelManager()
        self.booking = None
        self.room_id = None
        self.language_preference = None
    
    def set_language_preference(self, language_preference:str):
        self.language_preference = language_preference

    def set_booking(self, booking:Booking):
        self.booking = booking
    
    def set_room_id(self, room_id:int):
        self.room_id = room_id
    
    def get_language_preference(self):
        return self.language_preference
    
    def get_room_id(self):
        return self.room_id
    
    def get_booking(self):
        return self.booking
    
    def get_hotel_management(self):
        return self.hotel_management
    
    def set_llm(self, llm):
        self.llm = llm