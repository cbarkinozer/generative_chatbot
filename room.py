import sqlite3
import json
from datetime import datetime
import os

class HotelManager:
    def __init__(self, db_file='hotel.db', room_file='room.json'):
        if os.path.exists(db_file):
            os.remove(db_file)

        # Connect to the database and enable foreign key support
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.cursor.execute('PRAGMA foreign_keys = ON;')

        # Create the necessary tables
        self.create_tables()

        # Initialize the hotel by loading room data from JSON file
        self.initialize_rooms(room_file)

    # 1. Create the necessary tables if they don't exist
    def create_tables(self):
        try:
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Rooms (
                    room_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_type TEXT NOT NULL
                );
            ''')
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS Reservations (
                    reservation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    room_id INTEGER NOT NULL,
                    reservation_start_date DATE NOT NULL,
                    reservation_end_date DATE NOT NULL,
                    guest_name TEXT NOT NULL,
                    FOREIGN KEY (room_id) REFERENCES Rooms(room_id)
                );
            ''')
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error occurred while creating tables: {e}")
            self.conn.rollback()

    # 2. Populate the Rooms table based on JSON data
    def initialize_rooms(self, room_file):
        # Read and load JSON data with error handling
        try:
            with open(room_file, 'r') as file:
                room_data = json.load(file)
        except FileNotFoundError:
            print(f"Error: The file {room_file} does not exist.")
            return
        except json.JSONDecodeError:
            print(f"Error: Failed to parse {room_file}.")
            return

        # Insert room data into the Rooms table
        for room in room_data.get('rooms', []):
            room_type = room.get('room_type')
            count = room.get('count', 0)
            try:
                count = int(count)
            except ValueError:
                print(f"Error: Invalid room count in JSON: {room}")
                continue
            if room_type and count > 0:
                for _ in range(count):
                    try:
                        self.cursor.execute(
                            'INSERT INTO Rooms (room_type) VALUES (?)',
                            (room_type,)
                        )
                    except sqlite3.Error as e:
                        print(f"Error inserting room {room_type}: {e}")
                        self.conn.rollback()
                self.conn.commit()  # Commit once all rooms of a type are inserted
            else:
                print(f"Error: Invalid room entry in JSON: {room}")
        
        # Check data in tables
        self.cursor.execute('SELECT * FROM Rooms;')
        print(f"Current rooms: {self.cursor.fetchall()}")
        self.cursor.execute('SELECT * FROM Reservations;')
        print(f"Current reservations: {self.cursor.fetchall()}")
        self.conn.commit()

    # 3. Reserve a room if available for a given time period by room type
    def reserve_room(self, room_type, start_date, end_date):
        # Ensure date format is valid (YYYY-MM-DD)
        if not (self.is_valid_date_format(start_date) and self.is_valid_date_format(end_date)):
            print(f"Error: Dates must be in 'YYYY-MM-DD' format. Given: {start_date}, {end_date}")
            return None

        try:
            # Query to find an available room of the specified type
            self.cursor.execute('''
                SELECT room_id FROM Rooms
                WHERE room_type = ? AND room_id NOT IN (
                    SELECT room_id FROM Reservations
                    WHERE NOT (reservation_end_date < ? OR reservation_start_date > ?)
                ) LIMIT 1
            ''', (room_type, start_date, end_date))
            
            room = self.cursor.fetchone()
            
            if room:
                room_id = room[0]
                self.cursor.execute('''
                    INSERT INTO Reservations (room_id, reservation_start_date, reservation_end_date, guest_name)
                    VALUES (?, ?, ?, ?)
                ''', (room_id, start_date, end_date, "Guest"))
                self.conn.commit()
                print(f"Room {room_id} reserved from {start_date} to {end_date}")
                return room_id
            else:
                print(f"No available rooms for {room_type} between {start_date} and {end_date}")
                return None
        except sqlite3.Error as e:
            print(f"Error occurred while reserving room: {e}")
            self.conn.rollback()
            return None
    
    # Helper method to validate date format
    def is_valid_date_format(self, date_str):
        try:
            datetime.strptime(date_str, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    # 4. Reserve room by room_id directly
    def reserve_room_by_id(self, room_id, start_date, end_date):
        if not (self.is_valid_date_format(start_date) and self.is_valid_date_format(end_date)):
            print(f"Error: Dates must be in 'YYYY-MM-DD' format. Given: {start_date}, {end_date}")
            return None

        try:
            # Check if the room is already reserved during the requested dates
            self.cursor.execute('''
                SELECT 1 FROM Reservations
                WHERE room_id = ? AND reservation_start_date < ? AND reservation_end_date > ?
            ''', (room_id, end_date, start_date))
            
            room_reserved = self.cursor.fetchone()

            if room_reserved:
                print(f"Room {room_id} is already reserved between {start_date} and {end_date}.")
                return None

            # Reserve the room if no conflicts are found
            self.cursor.execute('''
                INSERT INTO Reservations (room_id, reservation_start_date, reservation_end_date, guest_name)
                VALUES (?, ?, ?, ?)
            ''', (room_id, start_date, end_date, "Guest"))
            
            self.conn.commit()
            print(f"Room {room_id} reserved from {start_date} to {end_date}")
            return room_id
        
        except sqlite3.Error as e:
            self.conn.rollback()
            print(f"An error occurred while reserving room {room_id}: {e}")
            return None

    # 5. Check available rooms for a given time period
    def check_room_availability(self, room_type, start_date, end_date):
        if not (self.is_valid_date_format(start_date) and self.is_valid_date_format(end_date)):
            print(f"Error: Dates must be in 'YYYY-MM-DD' format. Given: {start_date}, {end_date}")
            return []

        try:
            self.cursor.execute('''
                SELECT room_id FROM Rooms
                WHERE room_type = ? AND room_id NOT IN (
                    SELECT room_id FROM Reservations
                    WHERE reservation_end_date > ? AND reservation_start_date < ?
                )
            ''', (room_type, start_date, end_date))
            
            available_rooms = self.cursor.fetchall()
            
            if available_rooms:
                room_ids = [room[0] for room in available_rooms]
                print(f"Available rooms of type {room_type} from {start_date} to {end_date}: {room_ids}")
                return room_ids
            else:
                print(f"No available rooms of type {room_type} between {start_date} and {end_date}")
                return []
        
        except sqlite3.Error as e:
            print(f"An error occurred while checking room availability: {e}")
            return []

    # 6. Cancel a reservation based on room ID and dates
    def cancel_reservation(self, room_id, start_date, end_date):
        if not (self.is_valid_date_format(start_date) and self.is_valid_date_format(end_date)):
            print(f"Error: Dates must be in 'YYYY-MM-DD' format. Given: {start_date}, {end_date}")
            return

        try:
            self.cursor.execute('''
                DELETE FROM Reservations
                WHERE room_id = ? 
                AND DATE(reservation_start_date) = ? 
                AND DATE(reservation_end_date) = ?
            ''', (room_id, start_date, end_date))
            
            if self.cursor.rowcount > 0:
                print(f"Reservation for room {room_id} from {start_date} to {end_date} has been canceled.")
            else:
                print(f"No reservation found for room {room_id} from {start_date} to {end_date}.")
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            print(f"Error occurred while cancelling reservation: {e}")
            self.conn.rollback()

    # 7. Release past reservations (e.g., if the end date is in the past)
    def release_past_reservations(self):
        try:
            today = datetime.utcnow().strftime('%Y-%m-%d')  # Use UTC to avoid timezone issues
            
            self.cursor.execute('''
                DELETE FROM Reservations
                WHERE DATE(reservation_end_date) < ?
            ''', (today,))
            
            self.conn.commit()
            print("Released all rooms reserved for past dates.")
            
        except sqlite3.Error as e:
            print(f"Error occurred while releasing past reservations: {e}")
            self.conn.rollback()

    # Close the connection
    def close(self):
        try:
            self.conn.close()
        except sqlite3.Error as e:
            print(f"Error occurred while closing the connection: {e}")

if __name__ == "__main__":
    manager = HotelManager()
    # Test 1: Check available rooms (should return rooms initially as all are available)
    print("\nChecking room availability:")
    manager.check_room_availability('Single', '2024-09-25', '2024-09-30')  

    # Test 2: Reserve a room by type
    print("\nReserving a room by type:")
    manager.reserve_room('Single', '2024-09-25', '2024-09-30')  

    # Test 3: Check room availability again
    print("\nChecking room availability after reservation:")
    manager.check_room_availability('Single', '2024-09-25', '2024-09-30')  

    # Test 4: Cancel a reservation
    print("\nCancelling reservation:")
    manager.cancel_reservation(1, '2024-09-25', '2024-09-30')

    # Test 5: Release past reservations
    print("\nReleasing past reservations:")
    manager.release_past_reservations()

    # Close the manager (important to close the database connection)
    manager.close()
