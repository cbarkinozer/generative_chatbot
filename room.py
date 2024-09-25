import sqlite3
from datetime import datetime
import os
import json

class HotelManager:
    def __init__(self, db_name="hotel.db"):
        if os.path.exists(db_name):
            os.remove(db_name)
        self.conn = sqlite3.connect(db_name)
        self.create_tables()
        self.initialize_rooms(rooms_file="room.json")

    def create_tables(self):
        cursor = self.conn.cursor()

        # Room Types Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS room_types (
                            room_type TEXT PRIMARY KEY,
                            count INTEGER
                        )''')

        # Rooms Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS rooms (
                            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            room_type TEXT,
                            is_available INTEGER DEFAULT 1,
                            FOREIGN KEY (room_type) REFERENCES room_types(room_type)
                        )''')

        # Reservations Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS reservations (
                            reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                            full_name TEXT,
                            phone_number TEXT,
                            email TEXT,
                            start_date TEXT,
                            end_date TEXT,
                            guest_count INTEGER,
                            room_type TEXT,
                            number_of_rooms INTEGER,
                            payment_method TEXT,
                            include_breakfast INTEGER,
                            note TEXT,
                            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (room_type) REFERENCES room_types(room_type)
                        )''')

        # Reservation-Rooms Mapping Table
        cursor.execute('''CREATE TABLE IF NOT EXISTS reservation_rooms (
                            reservation_id INTEGER,
                            room_id INTEGER,
                            PRIMARY KEY (reservation_id, room_id),
                            FOREIGN KEY (reservation_id) REFERENCES reservations(reservation_id),
                            FOREIGN KEY (room_id) REFERENCES rooms(room_id)
                        )''')

        self.conn.commit()

    def initialize_rooms(self, rooms_file):
        with open(rooms_file, 'r') as f:
            room_data = json.load(f)

        cursor = self.conn.cursor()
        # Insert room types and their counts into room_types table
        for room in room_data['rooms']:
            room_type = room['room_type']
            count = room['count']
            cursor.execute('''INSERT OR IGNORE INTO room_types (room_type, count)
                              VALUES (?, ?)''', (room_type, count))
            # Add actual rooms based on room type count
            for _ in range(count):
                cursor.execute('''INSERT INTO rooms (room_type)
                                  VALUES (?)''', (room_type,))

        self.conn.commit()

    def is_valid_date_format(self, date_str):
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def check_room_availability(self, room_type, start_date, end_date):
        cursor = self.conn.cursor()
        cursor.execute('''SELECT r.room_id FROM rooms r
                          LEFT JOIN reservation_rooms rr ON r.room_id = rr.room_id
                          LEFT JOIN reservations res ON rr.reservation_id = res.reservation_id
                          WHERE r.room_type = ? AND r.is_available = 1
                          AND (res.start_date IS NULL OR res.end_date < ? OR res.start_date > ?)
                          LIMIT 1''', (room_type, start_date, end_date))
        room = cursor.fetchone()
        return room if room else None

    def reserve_room(self, full_name, phone_number, email, room_type, start_date, end_date, guest_count, number_of_rooms, payment_method, include_breakfast, note):
        if not self.is_valid_date_format(start_date) or not self.is_valid_date_format(end_date):
            return "Invalid date format. Please use YYYY-MM-DD."

        cursor = self.conn.cursor()
        room = self.check_room_availability(room_type, start_date, end_date)
        if room:
            room_id = room[0]
            # Create the reservation entry
            cursor.execute('''INSERT INTO reservations (full_name, phone_number, email, start_date, end_date, guest_count, room_type, number_of_rooms, payment_method, include_breakfast, note)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                           (full_name, phone_number, email, start_date, end_date, guest_count, room_type, number_of_rooms, payment_method, include_breakfast, note))
            reservation_id = cursor.lastrowid

            # Link reservation to the room
            cursor.execute('''INSERT INTO reservation_rooms (reservation_id, room_id)
                              VALUES (?, ?)''', (reservation_id, room_id))

            # Update room availability status
            cursor.execute('''UPDATE rooms SET is_available = 0 WHERE room_id = ?''', (room_id,))

            self.conn.commit()
            return f"Room {room_id} reserved from {start_date} to {end_date}."
        else:
            return "No available rooms for the selected type and dates."


    def cancel_reservation(self, room_id):
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM reservation_rooms WHERE room_id = ?''', (room_id,))
        cursor.execute('''DELETE FROM reservations WHERE room_id = ?''', (room_id,))
        cursor.execute('''UPDATE rooms SET is_available = 1 WHERE room_id = ?''', (room_id,))
        self.conn.commit()
        return f"Reservation for Room {room_id} has been canceled."

    def release_past_reservations(self):
        today = datetime.today().strftime('%Y-%m-%d')
        cursor = self.conn.cursor()
        cursor.execute('''DELETE FROM reservations WHERE end_date < ?''', (today,))
        cursor.execute('''UPDATE rooms SET is_available = 1
                          WHERE room_id IN (SELECT room_id FROM reservations WHERE end_date < ?)''', (today,))
        self.conn.commit()
        return "Past reservations released and rooms marked as available."


if __name__ == "__main__":
    hotel_manager = HotelManager()
    start_date = '2024-09-25'
    end_date = '2024-09-26'
    print(hotel_manager.reserve_room("Barkın Öz", "5365363636", "c.barkinozer@gmail.com", "suite", "2024-10-01", "2024-10-05", 2, 1, "credit card", True, "Planning to arrive between 00:00 and 02:00."))
    print(hotel_manager.reserve_room("Barkın Öz", "5365363636", "c.barkinozer@gmail.com", "suite", "2024-10-01", "2024-10-05", 2, 1, "credit card", True, "Planning to arrive between 00:00 and 02:00."))
    print(hotel_manager.reserve_room("Barkın Öz", "5365363636", "c.barkinozer@gmail.com", "suite", "2024-10-01", "2024-10-05", 2, 1, "credit card", True, "Planning to arrive between 00:00 and 02:00."))
    print(hotel_manager.reserve_room("Barkın Öz", "5365363636", "c.barkinozer@gmail.com", "suite", "2024-10-06", "2024-10-08", 2, 1, "credit card", True, "Planning to arrive between 00:00 and 02:00."))
    
