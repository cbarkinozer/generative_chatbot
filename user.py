from memory import Memory
from booking import Booking
from room import HotelManager

class User:
    def __init__(self, username):
        self.username = username
        self.llm = "llama3" #gemini-pro
        self.embedder = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        self.memory = Memory()
        self.hotel_management = HotelManager()
        self.booking = None
    
    def set_booking(self, booking:Booking):
        self.booking = booking
    
    def get_booking(self):
        return self.booking
    
    def get_hotel_management(self):
        return self.hotel_management
    
    def set_llm(self, llm):
        self.llm = llm