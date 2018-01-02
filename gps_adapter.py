import time
import random
import threading

class GPSAdapter:

    def __init__(self):
        pass

    def read_gps(self):
        waitms = random.randrange(100,2000) / 1000
        print("{} - read_gps (Sleep: {})".format(threading.current_thread().getName(), waitms))
        time.sleep(waitms)
        # throw random error
        failed = random.randrange(0,2)
        if failed == 1:
            return {
                "source": "gps",
                "value": None,
                "error": "Something went wrong"
            }
        return {
                "source": "gps",
                "value": {
                    "latitude": 12.12,
                    "longitude": 24.24
                }
            }
        

if __name__ == "__main__":
    gps = GPSAdapter()
    result = gps.read_gps()
    print("Result: {}".format(result))
