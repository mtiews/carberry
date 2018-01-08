#!/usr/bin/env python3

import json
import logging
import time
import datetime
import paho.mqtt.client as mqtt
from rx import Observer

class MQTTSink(Observer):
    def __init__(self, *, host="localhost", port=1883, clientid, topic_prefix):
        self._logger = logging.getLogger(__name__)
        self._host = host
        self._port = port
        self._clientid = clientid
        self._heartbeat_topic = topic_prefix + "/heartbeat"
        self._status_topic = topic_prefix + "/status"
        self._data_topic = topic_prefix + "/data"
        self._mqtt_client = None

    def __del__(self):
        self.dispose()

    def dispose(self):
        self._uninit_mqttclient()

    def heartbeat(self):
        self._ensure_connected()
        currentmillis = int(round(time.time() * 1000))
        payload = json.dumps({
                "timestamp": currentmillis, 
                "timestamp_str": datetime.datetime.utcfromtimestamp(currentmillis/1000).isoformat()
            })
        self._mqtt_client.publish(topic=self._heartbeat_topic, payload=payload, qos=1, retain=False)

    def submit_data(self, data):
        self._ensure_connected()
        payload = json.dumps(data)
        self._logger.debug("Submitting data '%s' to '%s'", payload, self._data_topic)
        self._mqtt_client.publish(topic=self._data_topic, payload=payload, qos=1, retain=False)

    def submit_status(self, *, status, status_text=None):
        self._ensure_connected()
        payload = json.dumps(self._create_status_message(status=status, status_text=status_text))
        self._logger.debug("Submitting status '%s' to '%s'", payload, self._data_topic)
        self._mqtt_client.publish(topic=self._status_topic, payload=payload, qos=1, retain=False)

    def _ensure_connected(self):
        if self._mqtt_client != None:
            return
        self._logger.info("Initializing MQTT Connection")
        
        def on_connect(mqttc, obj, flags, rc):
            if rc == 0:
                self._logger.info("Connection result '%s' ", mqtt.connack_string(rc))
                return
            self._logger.error("Connection result '%s': %s", str(rc), mqtt.connack_string(rc))

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                self._logger.warning("Unexpected MQTT disconnection. Will auto-reconnect")

        self._mqtt_client = mqtt.Client(self._clientid)
        self._mqtt_client.will_set(self._status_topic, payload=json.dumps(self._create_status_message(status="offline", status_text="LWT message")), qos=1, retain=False)
        self._mqtt_client.on_connect = on_connect
        self._mqtt_client.on_disconnect = on_disconnect
        self._mqtt_client.connect(self._host, self._port, 60)
        self._mqtt_client.loop_start()

    def _uninit_mqttclient(self):
        self._logger.info("Disconnecting MQTT")
        if self._mqtt_client is None:
            return
        self.submit_status(status="offline")
        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()
        self._mqtt_client = None

    def _create_status_message(self, *, status, status_text=None):
        currentmillis = int(round(time.time() * 1000))
        return {
            "status": status,
            "status_text": status_text,
            "timestamp": currentmillis, 
            "timestamp_str": datetime.datetime.utcfromtimestamp(currentmillis/1000).isoformat()
        }
        
    def on_next(self, value):
        self.submit_data(value)

    def on_completed(self):
        pass

    def on_error(self, error):
        self._logger.info("Observer error received: %s", error)

if __name__ == "__main__":
    # only for testing
    import time
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")

    sink = MQTTSink(clientid="mqttsink_test", topic_prefix="mqttsink_test")
    sink.heartbeat()

    sink.on_next({"sensor": "sensor1", "value": 1000})
    sink.on_next({"sensor": "sensor1", "value": 1000})
    sink.on_completed()
    sink.on_error("Something went wrong")
    sink.heartbeat()

    time.sleep(3)
    sink.dispose()
