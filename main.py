import json
import logging
import time

from rx import Observable, Observer

from mqtt_sink import MQTTSink
from obd2_adapter import OBD2Adapter
from gps_adapter import GPSAdapter

# Configuration values - locally fixed
MQTT_CLIENT_NAME = "carberry"
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = MQTT_CLIENT_NAME

# Configuration values - potentially from remote configuration
OBD2_SENSORS = ["sensor1", "sensor2", "sensor3"]
OBD2_POLL_INTERVAL = 1000
GPS_POLL_INTERVAL = 2 * 1000

class PipelineLog(Observer):
    def __init__(self, pipeline_name):
        self._pipeline_name = pipeline_name
        self._logger = logging.getLogger(__name__)
        
    def on_next(self, data):
        pass
    
    def on_completed(self):
        pass
    
    def on_error(self, error):
        self._logger.error("Error in pipeline '{}': {}".format(self._pipeline_name, error))

class CarDataToMqtt:
    def __init__(self):
        self._logger = logging.getLogger(__name__)
        
        self._sink = MQTTSink(clientid = MQTT_CLIENT_NAME, topic_prefix = MQTT_TOPIC_PREFIX)

        self._obd2 = None
        self._obd2_subscription = None
        self._gps = None
        self._gps_subscription = None      

        self._init_pipelines()

    def initialize(self): 
        self._sink.initialize()
        self._init_pipelines()

    def _init_pipelines(self):
        # OBD2
        self._obd2 = OBD2Adapter(OBD2_SENSORS)
        self._obd2_subscription = \
            Observable.interval(OBD2_POLL_INTERVAL) \
                .map(lambda s: self._obd2.read_sensors()) \
                .flat_map(lambda l: Observable.from_(l)) \
                .do_action(PipelineLog('obd2')) \
                .retry() \
                .subscribe(self._sink)
        
        # GPS
        self._gps = GPSAdapter()
        self._obd2_subscription = \
        Observable.interval(GPS_POLL_INTERVAL) \
            .map(lambda s: self._gps.read_gps()) \
            .do_action(PipelineLog('obd2')) \
            .retry() \
            .subscribe(self._sink)

if __name__ == "__main__":
    logging.basicConfig(level = logging.DEBUG, format = "%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")
    
    logger = logging.getLogger("carberry")
    logger.info("Starting module...")
    
    datatransfer = CarDataToMqtt()
    datatransfer.initialize()

    while 1:
        time.sleep(10)   
    
    logger.info("...done")
    