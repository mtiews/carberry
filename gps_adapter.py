#!/usr/bin/env python3

import time
import datetime
import logging
import threading

from gps3 import gps3

class GPSAdapter:

    def __init__(self, *, configuration):
        self._logger = logging.getLogger(__name__)
        self._gps_socket = None
        
    def __del__(self):
        self.dispose()

    def dispose(self):
        if self._gps_socket is None:
            return
        self._gps_socket.close()
        self._gps_socket = None

    def _ensure_connected(self):
        if self._gps_socket is not None:
            return
        self._gps_socket = gps3.GPSDSocket()
        self._gps_socket.connect()
        self._gps_socket.watch()

    def read_gps(self):
        self._ensure_connected()
        gpsdata = gps3.DataStream()
        count = 0
        for raw_gpsdata in self._gps_socket:
            if raw_gpsdata:
                gpsdata.unpack(raw_gpsdata)
                if gpsdata.TPV["lat"] != "n/a":
                    timestamp = int(round(time.time() * 1000))
                    timestamp_str = datetime.datetime.utcfromtimestamp(timestamp/1000).isoformat()
                    return {
                        "source": "gps",
                        # See http://www.catb.org/gpsd/gpsd_json.html for description
                        "value": gpsdata.TPV,
                        "timestamp": timestamp,
                        "timestamp_str": timestamp_str
                    }
            else:
                time.sleep(0.1)
            count = count + 1
            if count > 100:
                break
        timestamp = int(round(time.time() * 1000))
        timestamp_str = datetime.datetime.utcfromtimestamp(timestamp/1000).isoformat()
        return {
            "source": "gps",
            "value": None,
            "timestamp": timestamp,
            "timestamp_str": timestamp_str
        }

if __name__ == "__main__":
    # only for testing
    gps = GPSAdapter(configuration={})
    i = 0
    while i < 100:
        result = gps.read_gps()
        print("Result: {}".format(result))
        i = i + 1
        time.sleep(1)

    