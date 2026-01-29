import time
import threading
import pyodbc


def loading_animation(stop_event):
    while not stop_event.is_set():
        for dots in range(4):
            print("\rConnecting" + "." * dots + "   ", end="", flush=True)
            time.sleep(0.2)

def connect_database():
    conn_str = ("connection credentials")

    stop_event = threading.Event()
    animation_thread = threading.Thread(target=loading_animation, args=(stop_event,))
    animation_thread.start()

    try:
        conn = pyodbc.connect(conn_str)
        stop_event.set()
        animation_thread.join()
        print("\rConnecting to database... Done!", flush=True)
        return conn
    except Exception as error:
        stop_event.set()
        animation_thread.join()
        print(f"\rConnecting to database... Failed!", flush=True)
        print(f"Error connecting to the database: {str(error)}")
        return None