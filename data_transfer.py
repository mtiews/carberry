import logging

from rx import Observable, Observer

class PipelineLog(Observer):
    def __init__(self, pipeline_name):
        self._pipeline_name = pipeline_name
        self._logger = logging.getLogger(__name__)

    def on_next(self, value):
        pass

    def on_completed(self):
        pass

    def on_error(self, error):
        self._logger.error("Error in pipeline '%s': %s", self._pipeline_name, error)

class DataTransfer:
    def __init__(self, *, mqtt_sink, obd2_adapter, gps_adapter):
        self._logger = logging.getLogger(__name__)
        self._sink = mqtt_sink
        self._initialized = False
        self._heartbeat_subscription = None
        self._obd2 = obd2_adapter
        self._obd2_subscription = None
        self._gps = gps_adapter
        self._gps_subscription = None

    def __del__(self):
        self._stop_pipelines()

    def start(self, *, configuration):
        self._start_pipelines(configuration)

    def stop(self):
        self._stop_pipelines()

    def _start_pipelines(self, configuration):
        if self._initialized == True:
            return

        self._logger.info("Starting Pipelines")
        # Heartbeat
        self._heartbeat_subscription = \
            Observable.interval(configuration["heartbeat_interval"] * 1000) \
                .map(lambda s: self._sink.heartbeat()) \
                .do_action(PipelineLog('heartbeat')) \
                .retry() \
                .subscribe(on_next=lambda i: i) # nothing to do here
        # OBD2
        self._obd2_subscription = \
            Observable.interval(configuration["obd2_poll_interval"] * 1000) \
                .map(lambda s: self._obd2.read_sensors()) \
                .flat_map(lambda l: Observable.from_(l)) \
                .do_action(PipelineLog('obd2')) \
                .retry() \
                .subscribe(self._sink)
        # GPS
        self._gps_subscription = \
            Observable.interval(configuration["gps_poll_interval"] * 1000) \
                .map(lambda s: self._gps.read_gps()) \
                .do_action(PipelineLog('gps')) \
                .retry() \
                .subscribe(self._sink)
        self._initialized = True
        
    def _stop_pipelines(self):
        self._logger.info("Stopping Pipelines")
        if self._obd2_subscription != None:
            self._obd2_subscription.dispose()
        if self._heartbeat_subscription != None:
            self._heartbeat_subscription.dispose()
        if self._gps_subscription != None:
            self._gps_subscription.dispose()
        self._initialized = False

if __name__ == "__main__":
    # only for testing
    import time 
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")

    mqtt = type("", (object,), { "initialize": lambda: print("mqtt_initialize"), "heartbeat": lambda: print("mqtt_heartbeat"), "on_next": lambda d: print("mqtt_on_next > " + str(d))})
    obd2 = type("", (object,), { "read_sensors": lambda: ["read_sensors_result1", "read_sensors_result2"]})
    gps = type("", (object,), { "read_gps": lambda: "read_gps_result"})
    dt = DataTransfer(mqtt_sink=mqtt, obd2_adapter=obd2, gps_adapter=gps)
    
    config = { "heartbeat_interval": 1, "obd2_poll_interval": 1, "gps_poll_interval": 1}
    dt.start(configuration=config)
    time.sleep(3)
    dt.stop()
