#!/usr/bin/env python3

import datetime
import logging
import threading
import time

import obd

class OBD2Adapter:

    def __init__(self, *, configuration):
        self._logger = logging.getLogger(__name__)
        if isinstance(configuration["sensors"], list):
            self._sensors_to_read = configuration["sensors"]
        else:
            self._sensors_to_read = [configuration["sensors"]]
        self._connection = None

    def __del__(self):
        self.dispose()

    def dispose(self):
        if self._connection is None:
            return
        self._connection.close()
        self._connection = None

    def _ensure_connected(self):
        if self._connection is None:
            self._logger.info("Initializing OBD2 connection")
            self._connection = obd.OBD()
        if self._connection.is_connected() is not True:
            self._logger.error("Failed to connect to OBD2")
            self._connection.close()
            self._connection = None
            return False
        else:
            return True
    
    def read_sensors(self):
        print("{} - read_values".format(threading.current_thread().getName()))
        for sensor_name in self._sensors_to_read:
            yield self.read_sensor(sensor_name)

    def read_sensor(self, sensor_name):
        try:
            if self._ensure_connected() is not True:
                return self._create_sensor_data_message(sensor_name=sensor_name, error="OBD2 not connected")
            result = self._connection.query(obd.commands[sensor_name])
            svalue = None
            sunit = None
            if not result.is_null():
                try:
                    svalue = result.value.magnitude
                    sunit = str(result.value.units)
                except AttributeError:
                    svalue = str(result.value)
            return self._create_sensor_data_message(sensor_name=sensor_name, value=svalue, unit=sunit)
        except Exception as ex:
            return self._create_sensor_data_message(sensor_name=sensor_name, error=str(ex))

    def _create_sensor_data_message(self, *, sensor_name, value=None, unit=None, error=None):
        timestamp = int(round(time.time() * 1000))
        timestamp_str = datetime.datetime.utcfromtimestamp(timestamp/1000).isoformat()
        return {
            "source": "obd2",
            "sensor": sensor_name,
            "value": value,
            "unit": unit,
            "timestamp": timestamp,
            "timestamp_str": timestamp_str,
            "error": error
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")
    # only for testing
    obd2 = OBD2Adapter(configuration={"sensors": "RPM"})
    for s in obd2.read_sensors():
        print("Sensordata: {}".format(s))
    obd2.dispose()

    obd2 = OBD2Adapter(configuration={"sensors": ["STATUS", "RPM", "SPEED"]})
    for s in obd2.read_sensors():
        print("Sensordata: {}".format(s))
    obd2.dispose()
