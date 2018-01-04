#!/usr/bin/env python3

import time
import datetime
import random
import threading

class OBD2Adapter:

    def __init__(self, *, configuration):
        if isinstance(configuration["sensors"], list):
            self._sensors_to_read = configuration["sensors"]
        else:
            self._sensors_to_read = [configuration["sensors"]]

    def read_sensors(self):
        print("{} - read_values".format(threading.current_thread().getName()))
        for sensor_name in self._sensors_to_read:
            yield self.read_sensor(sensor_name)

    def read_sensor(self, sensor_name):
        waitms = random.randrange(100, 2000) / 1000
        time.sleep(waitms)
        # throw random error
        timestamp = int(round(time.time() * 1000))
        timestamp_str = datetime.datetime.utcfromtimestamp(timestamp/1000).isoformat()
        failed = random.randrange(0, 2)
        if failed == 1:
            return {
                "source": "obd2",
                "sensor": sensor_name,
                "value": None,
                "error": "Something went wrong",
                "timestamp": timestamp,
                "timestamp_str": timestamp_str
            }
        return {
            "source": "obd2",
            "sensor": sensor_name,
            "value": waitms,
            "timestamp": timestamp,
            "timestamp_str": timestamp_str
        }

if __name__ == "__main__":
    # only for testing
    obd2 = OBD2Adapter(configuration={"sensors": "single"})
    for s in obd2.read_sensors():
        print("Sensordata: {}".format(s))

    obd2 = OBD2Adapter(configuration={"sensors": ["list1", "list2", "list3"]})
    for s in obd2.read_sensors():
        print("Sensordata: {}".format(s))
