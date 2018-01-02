import time
import random
import threading

class OBD2Adapter:

    def __init__(self, sensors_to_read):
        if isinstance(sensors_to_read, list):
            self._sensors_to_read = sensors_to_read
        else:
            self._sensors_to_read = [sensors_to_read]
    
    # TODO: Change to generator (yield)
    def read_sensors(self):
        print("{} - read_values".format(threading.current_thread().getName()))
        for sensor_name in self._sensors_to_read:
            yield self.read_sensor(sensor_name)
    
    def read_sensor(self, sensor_name):
        waitms = random.randrange(100,2000) / 1000
        print("{} - read_sensor: {} (Sleep: {})".format(threading.current_thread().getName(), sensor_name, waitms))
        time.sleep(waitms)
        # throw random error
        failed = random.randrange(0,2)
        if failed == 1:
            return {
                "source": "obd2",
                "sensor": sensor_name,
                "value": None,
                "error": "Something went wrong"
            }
        return {
                "source": "obd2",
                "sensor": sensor_name,
                "value": waitms
            }    

if __name__ == "__main__":
    obd2 = OBD2Adapter("single")
    result = obd2.read_sensors()
    print("Result: {}".format(result))

    obd2 = OBD2Adapter(["list1", "list2", "list3"])
    result = obd2.read_sensors()
    print("Result: {}".format(result))
