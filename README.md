# Flight-Reservation-System
**Flight Reservation Database System – COMP2016 Database Management Group Project**

## Project Description

This is a flight reservation database application that supports multi-leg flight bookings (1 to 3 connected flights). The system is built with **Python** and **Oracle Database**, and uses **PL/SQL triggers** to maintain data integrity.

### Key Features

- Flight Management (Add / Delete / View flights)
- Multi-city Flight Search (with maximum connections and travel time constraints)
- Flight Booking (all-or-nothing booking)
- Booking Cancellation
- Automatic seat availability update using database triggers
- Fare calculation with discounts for connecting flights (90% for 2 flights, 75% for 3 flights)

## Technologies Used

- **Python 3**
- **Oracle Database** (oracledb)
- **PL/SQL Triggers**
- SSH Tunnel (for remote database connection)

## Project Structure

- `FlightManager.py` – Main application
- `db_insert.sql` – Create tables, insert sample data & triggers
- `db_drop.sql` – Drop all tables and triggers
- `requirements.txt` – Python dependencies


## How to Run

1. Install the required packages:
   ```bash
   pip install -r requirements.txt
2. Make sure you have access to the Oracle database.
3. Run the program:
   python FlightManager.py

## Database Design
The system includes the following main tables:

- CUSTOMER – Customer information
- FLIGHT – Flight details and seat availability
- BOOKING – Booking records
- BOOKING_CONNECT_FLIGHT – Connection between bookings and flights

## Triggers

- Check seat availability before booking
- Automatically decrease available seats after successful booking
- Automatically increase available seats after cancellation
