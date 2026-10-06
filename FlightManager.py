import warnings
warnings.filterwarnings('ignore', 'TripleDES has been moved')

import pwinput
from colorama import Fore, Style
from types import SimpleNamespace

import atexit

from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError
import oracledb

''' Global variables'''
tunnel: SSHTunnelForwarder = None
cursor: oracledb.Cursor = None
connection: oracledb.Connection = None

db_info = SimpleNamespace(
    gateway = "faith.comp.hkbu.edu.hk",
    gw_port = 22,
    ora_host = "orasrv1.comp.hkbu.edu.hk",
    ora_port = 1521,
    srv_name = "pdborcl"
)

def on_exit()->None:
    """Callback function that closes all connections when program terminates."""
    try:
        cursor.close()
    except:
        pass
    try:
        connection.close()
    except:
        pass
    try:
        tunnel.stop()
    except:
        pass
    print("\n\nAll connections are closed. Good bye!\n\n")

def login_ssh_tunnel()->None:
    """Creates an SSH tunnel."""
    use = input("\nDo you want to use SSH Tunnel? (Y/N) ").strip()
    if len(use) == 0 or (use[0] not in "Yy"):
        return 
    
    username = input("Enter DB username:").strip()
    password = pwinput.pwinput(prompt="Enter DB password:")

    global tunnel

    try:
        tunnel = SSHTunnelForwarder(
            (db_info.gateway, db_info.gw_port),
            ssh_username = username, 
            ssh_password = password, 
            remote_bind_address = (db_info.ora_host, db_info.ora_port),
            local_bind_address = ("localhost", 0))

        tunnel.start()
        db_info.ora_host = "localhost"
        db_info.ora_port = tunnel.local_bind_port
        print(Fore.LIGHTCYAN_EX + f"Tunnel established at localhost:{tunnel.local_bind_port}\n" + Style.RESET_ALL)

    except (ValueError, BaseSSHTunnelForwarderError) as ex:
        print(ex)
        print(Fore.RED + "Could not enable the SSH tunnel." + Style.RESET_ALL)
        exit()

def login_db()->None:
    username = "f4238422" 
    password = "f4238422"

    global connection, cursor

    dsn = f"{db_info.ora_host}:{db_info.ora_port}/{db_info.srv_name}"

    try:
        connection = oracledb.connect(user = username, password = password, dsn=dsn)
        cursor = connection.cursor()
        
        cursor.execute("SELECT banner FROM v$version")
        print(Fore.LIGHTCYAN_EX + f"\nConnected to {cursor.fetchone()[0]}\n" + Style.RESET_ALL)

    except oracledb.DatabaseError as ex:
        print(Fore.RED + "Invalid username or password. Login denied." + Style.RESET_ALL)
        exit()

def show_all_flights():
    """(1) Show all flights information."""
    cursor.execute("SELECT Flight_No, Source, Dest, Depart, Arrive, Fare, Seat_Limit FROM FLIGHT ORDER BY Flight_No")
    rows = cursor.fetchall()
    
    if len(rows) == 0:
        print(Fore.YELLOW + "No flights found." + Style.RESET_ALL)
    else:
        print(Fore.CYAN)
        print("\n" + "=" * 110)
        print(f"{'Flight No':<10} {'Source':<15} {'Destination':<15} {'Departure Time':<25} {'Arrival Time':<25} {'Fare':<8} {'Seats':<6}")
        print("=" * 110)
        for row in rows:
            print(f"{row[0]:<10} {row[1]:<15} {row[2]:<15} {str(row[3]):<25} {str(row[4]):<25} {row[5]:<8} {row[6]:<6}")
        print("=" * 110 + Style.RESET_ALL)

def show_flight_details():
    """(2) Show flight details by flight number."""
    flight_no = input("Enter flight number: ").strip().upper()
    
    cursor.execute("SELECT Flight_No, Source, Dest, Depart, Arrive, Fare, Seat_Limit FROM FLIGHT WHERE Flight_No = :1", [flight_no])
    row = cursor.fetchone()
    
    if row is None:
        print(Fore.RED + f"Flight {flight_no} not found." + Style.RESET_ALL)
    else:
        print(Fore.YELLOW)
        print("\n" + "=" * 50)
        print(f"Flight No:       {row[0]}")
        print(f"From:            {row[1]}")
        print(f"To:              {row[2]}")
        print(f"Departure Time:  {row[3]}")
        print(f"Arrival Time:    {row[4]}")
        print(f"Fare:            ${row[5]}")
        print(f"Seats Available: {row[6]}")
        print("=" * 50 + Style.RESET_ALL)

def add_flight():
    """(3) Add a new flight."""
    print("\nFormat: FlightNo, Source, Dest, Depart(YYYY/MM/DD HH24:MI:SS), Arrive(YYYY/MM/DD HH24:MI:SS), Fare, Seats")
    print("Example: CX108, HK, LA, 2026/03/15 08:00:00, 2026/03/15 20:00:00, 9000, 3")
    
    data = input("-> ").strip().split(',')
    if len(data) < 7: 
        print(Fore.RED + "Invalid input. Please provide all 7 fields." + Style.RESET_ALL)
        return
    
    try:
        cursor.execute("""INSERT INTO FLIGHT (Flight_No, Source, Dest, Depart, Arrive, Fare, Seat_Limit) 
                          VALUES (:1, :2, :3, TO_DATE(:4,'YYYY/MM/DD HH24:MI:SS'), TO_DATE(:5,'YYYY/MM/DD HH24:MI:SS'), :6, :7)""", data)
        connection.commit()
        print(Fore.GREEN + f"Successfully added flight {data[0]}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Failed to add flight: {e}" + Style.RESET_ALL)
        connection.rollback()

def delete_flight():
    """(4) Delete a flight."""
    show_all_flights()
    print("-" * 40)
    flight_no = input("Enter flight number to delete: ").strip().upper()
    
    try:
        cursor.execute("DELETE FROM FLIGHT WHERE Flight_No = :1", [flight_no])
        connection.commit()
        if cursor.rowcount > 0:
            print(Fore.GREEN + f"Successfully deleted flight {flight_no}" + Style.RESET_ALL)
        else:
            print(Fore.YELLOW + f"Flight {flight_no} not found." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Failed to delete flight: {e}" + Style.RESET_ALL)
        connection.rollback()

def search_connections():
    """(5) Search connections (source, dest, max legs, max hours)."""
    print()
    source = input("Source city: ").strip()
    dest = input("Destination city: ").strip()
    max_legs = int(input("Max connections (1-3): ").strip())
    max_hours = float(input("Max travel hours: ").strip())
    
    if max_legs < 1 or max_legs > 3:
        print(Fore.RED + "Max connections must be between 1 and 3." + Style.RESET_ALL)
        return
    
    results = []
    
    # Direct flights (1 leg) - no time filter first to debug
    cursor.execute("""
        SELECT Flight_No, Fare, Depart, Arrive 
        FROM FLIGHT 
        WHERE Source=:1 AND Dest=:2
    """, [source, dest])
    
    for row in cursor.fetchall():
        # Print debug info
        print(Fore.YELLOW + f"Found flight: {row[0]}, Depart: {row[2]}, Arrive: {row[3]}" + Style.RESET_ALL)
        results.append((row[0], row[1]))
    
    # Two flights (2 legs)
    if max_legs >= 2:
        cursor.execute("""
            SELECT f1.Flight_No, f2.Flight_No, (f1.Fare + f2.Fare)*0.9
            FROM FLIGHT f1 
            JOIN FLIGHT f2 ON f1.Dest = f2.Source 
            WHERE f1.Source=:1 AND f2.Dest=:2 
            AND f2.Depart > f1.Arrive
        """, [source, dest])
        
        for row in cursor.fetchall():
            results.append((f"{row[0]}->{row[1]}", int(row[2])))
    
    # Three flights (3 legs)
    if max_legs >= 3:
        cursor.execute("""
            SELECT f1.Flight_No, f2.Flight_No, f3.Flight_No,
                   (f1.Fare + f2.Fare + f3.Fare)*0.75
            FROM FLIGHT f1 
            JOIN FLIGHT f2 ON f1.Dest = f2.Source
            JOIN FLIGHT f3 ON f2.Dest = f3.Source
            WHERE f1.Source=:1 AND f3.Dest=:2 
            AND f2.Depart > f1.Arrive
            AND f3.Depart > f2.Arrive
        """, [source, dest])
        
        for row in cursor.fetchall():
            results.append((f"{row[0]}->{row[1]}->{row[2]}", int(row[3])))
    
    print(Fore.CYAN + f"\nTotal {len(results)} choice(s):" + Style.RESET_ALL)
    if len(results) == 0:
        print(Fore.YELLOW + "No flights found matching your criteria." + Style.RESET_ALL)
    else:
        for i, (route, fare) in enumerate(results, 1):
            print(f"({i}) {route}, fare: ${fare}")

def book_flight():
    """(6) Book flights (all-or-nothing booking)."""
    print("\nFormat: CustomerID, Flight1, Flight2, Flight3 (up to 3 flights)")
    print("Example: C01, CX105, CX104")
    
    raw = input("-> ").strip().split(',')
    if len(raw) < 2:
        print(Fore.RED + "Invalid input. At least CustomerID and one flight required." + Style.RESET_ALL)
        return
    
    customer_id = raw[0].strip()
    flight_nos = [f.strip() for f in raw[1:]]
    num_flights = len(flight_nos)
    
    if num_flights < 1 or num_flights > 3:
        print(Fore.RED + "Number of flights must be between 1 and 3." + Style.RESET_ALL)
        return
    
    # Generate booking ID
    cursor.execute("SELECT COUNT(*) FROM BOOKING")
    booking_id = "B" + str(cursor.fetchone()[0] + 1)
    
    try:
        # Calculate total fare with discount
        placeholders = ','.join([':' + str(i+1) for i in range(num_flights)])
        cursor.execute(f"SELECT SUM(Fare) FROM FLIGHT WHERE Flight_No IN ({placeholders})", flight_nos)
        total_fare_sum = cursor.fetchone()[0]
        
        if total_fare_sum is None:
            print(Fore.RED + "One or more flight numbers not found." + Style.RESET_ALL)
            return
        
        # Apply discount: 1 flight=100%, 2 flights=90%, 3 flights=75%
        discount = 1.0 if num_flights == 1 else (0.9 if num_flights == 2 else 0.75)
        total_fare = int(total_fare_sum * discount)
        
        # Insert booking
        cursor.execute("INSERT INTO BOOKING (Booking_id, Num_flight, Total_fare, Customer_ID) VALUES (:1, :2, :3, :4)",
                      [booking_id, num_flights, total_fare, customer_id])
        
        # Insert connections (triggers will check seat availability and decrement seats)
        for idx, flight_no in enumerate(flight_nos, 1):
            cursor.execute("INSERT INTO BOOKING_CONNECT_FLIGHT (Booking_id, Flight_No, Connect_order) VALUES (:1, :2, :3)",
                          [booking_id, flight_no, idx])
        
        connection.commit()
        print(Fore.GREEN + f"Successfully booked for {customer_id}, booking ID is {booking_id}" + Style.RESET_ALL)
        
    except oracledb.DatabaseError as e:
        connection.rollback()
        error_msg = str(e)
        if "is full" in error_msg:
            print(Fore.RED + "Failed to book: One or more flights are fully booked." + Style.RESET_ALL)
        else:
            print(Fore.RED + f"Failed to book: {error_msg}" + Style.RESET_ALL)
    except Exception as e:
        connection.rollback()
        print(Fore.RED + f"Failed to book: {e}" + Style.RESET_ALL)

def cancel_booking():
    """(7) Cancel booking."""
    customer_id = input("Customer ID: ").strip()
    booking_id = input("Booking ID: ").strip()
    
    try:
        # Check if booking exists
        cursor.execute("SELECT Booking_id FROM BOOKING WHERE Booking_id = :1 AND Customer_ID = :2", [booking_id, customer_id])
        if cursor.fetchone() is None:
            print(Fore.YELLOW + f"Booking {booking_id} for customer {customer_id} not found or already cancelled." + Style.RESET_ALL)
            return
        
        # Delete booking (ON DELETE CASCADE removes from BOOKING_CONNECT_FLIGHT, trigger increases seats)
        cursor.execute("DELETE FROM BOOKING WHERE Booking_id = :1 AND Customer_ID = :2", [booking_id, customer_id])
        connection.commit()
        print(Fore.GREEN + f"Booking {booking_id} for customer {customer_id} is cancelled." + Style.RESET_ALL)
        
    except Exception as e:
        connection.rollback()
        print(Fore.RED + f"Error cancelling booking: {e}" + Style.RESET_ALL)

def print_menu():
    """Display the main menu."""
    print(Fore.CYAN)
    print("\n" + "=" * 60)
    print("           FLIGHT RESERVATION SYSTEM")
    print("=" * 60)
    print("(1) Show all flights")
    print("(2) Show flight details by number")
    print("(3) Add a new flight")
    print("(4) Delete a flight")
    print("(5) Search connections (source, dest, max legs, max hours)")
    print("(6) Book flights")
    print("(7) Cancel booking")
    print("(8) Quit")
    print("=" * 60 + Style.RESET_ALL)

# Main program
atexit.register(on_exit)

login_ssh_tunnel()
login_db()

print(Fore.GREEN + "\nWelcome to Flight Manager!" + Style.RESET_ALL)

while True:
    print_menu()
    option = input("Please choose an option (1-8): ").strip()
    
    if option == "1":
        show_all_flights()
    elif option == "2":
        show_flight_details()
    elif option == "3":
        add_flight()
    elif option == "4":
        delete_flight()
    elif option == "5":
        search_connections()
    elif option == "6":
        book_flight()
    elif option == "7":
        cancel_booking()
    elif option == "8":
        print(Fore.YELLOW + "\nThank you for using Flight Manager!" + Style.RESET_ALL)
        break
    else:
        print(Fore.RED + "Invalid option. Please choose 1-8." + Style.RESET_ALL)
    
    print("\n" + "-" * 40)
    input("Press Enter to continue...")
