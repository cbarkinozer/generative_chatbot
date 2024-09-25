import sqlite3
from datetime import datetime
import os

class HotelManager:
    def __init__(self, db_name="hotel.db"):
        if os.path.exists(db_name):
            os.remove(db_name)
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.initialize_rooms()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (
                            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            room_type TEXT,
                            room_status TEXT
                          )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS reservations (
                            reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            room_id INTEGER,
                            start_date TEXT,
                            end_date TEXT,
                            FOREIGN KEY (room_id) REFERENCES rooms(room_id)
                          )''')
        self.conn.commit()

    def initialize_rooms(self):
        cursor = self.conn.cursor()
        cursor.execute('''INSERT INTO rooms (room_type, room_status)
                          SELECT 'single', 'available' UNION ALL
                          SELECT 'double', 'available' UNION ALL
                          SELECT 'suite', 'available'
                          ON CONFLICT DO NOTHING''')
        self.conn.commit()

    def is_valid_date_format(self, date_str):
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def check_room_availability(self, room_id, start_date, end_date):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT COUNT(*) FROM reservations
                          WHERE room_id = ? AND 
                          (? BETWEEN start_date AND end_date
                           OR ? BETWEEN start_date AND end_date)''', 
                       (room_id, start_date, end_date))
        return cursor.fetchone()[0] == 0

    def reserve_room_by_id(self, room_id, start_date, end_date):
        if not self.is_valid_date_format(start_date) or not self.is_valid_date_format(end_date):
            return "Invalid date format. Please use YYYY-MM-DD."
        
        cursor = self.conn.cursor()
        cursor.execute('SELECT room_status FROM rooms WHERE room_id = ?', (room_id,))
        room_status = cursor.fetchone()
        
        if room_status and room_status[0] == 'available':
            if self.check_room_availability(room_id, start_date, end_date):
                cursor.execute('''INSERT INTO reservations (room_id, start_date, end_date) 
                                  VALUES (?, ?, ?)''', (room_id, start_date, end_date))
                cursor.execute('''UPDATE rooms SET room_status = 'reserved' WHERE room_id = ?''', (room_id,))
                self.conn.commit()
                return f"Room {room_id} reserved from {start_date} to {end_date}."
            else:
                return "Room is not available for the given dates."
        else:
            return "Room is not available."

    def cancel_reservation(self, room_id):
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM reservations WHERE room_id = ?''', (room_id,))
        cursor.execute('''UPDATE rooms SET room_status = 'available' WHERE room_id = ?''', (room_id,))
        self.conn.commit()
        return f"Reservation for Room {room_id} has been canceled."

    def release_past_reservations(self):
        today = datetime.today().strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM reservations WHERE end_date < ?''', (today,))
        cursor.execute('''UPDATE rooms SET room_status = 'available'
                          WHERE room_id IN (SELECT room_id FROM reservations WHERE end_date < ?)''', (today,))
        self.conn.commit()
        return "Past reservations released and rooms marked as available."


if __name__ == "__main__":
    hotel_manager = HotelManager()
    room_id = 1
    room_type = "single"
    start_date = '2024-09-25'
    end_date = '2024-09-30'
    print(hotel_manager.reserve_room_by_id(room_id, start_date, end_date))
    print(hotel_manager.check_room_availability(1, start_date, end_date))
    print(hotel_manager.cancel_reservation(room_id))
    print(hotel_manager.check_room_availability(1, start_date, end_date))

