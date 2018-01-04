#!/usr/bin/env python3

import json
import logging
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

    def start(self):
        self._init_mqttclient()

    def stop(self):
        self._uninit_mqttclient()

    def heartbeat(self):
        self._mqtt_client.publish(topic=self._heartbeat_topic, payload=json.dumps({"timestamp": datetime.datetime.utcnow().isoformat()}), qos=1, retain=False)

    def __del__(self):
        self._uninit_mqttclient()

    def _init_mqttclient(self):
        self._logger.info("Initializing MQTT Connection")
        if self._mqtt_client != None:
            self._logger.info("Client already initialized, nothing to do")
            return

        def on_connect(mqttc, obj, flags, rc):
            if rc == 0:
                self._logger.info("Connection result '%s' ", mqtt.connack_string(rc))
                self._mqtt_client.publish(topic=self._status_topic, payload=json.dumps(self._create_status_message("online")), qos=1, retain=False)
                return
            self._logger.error("Connection result '%s': %s", str(rc), mqtt.connack_string(rc))

        def on_disconnect(client, userdata, rc):
            if rc != 0:
                self._logger.warning("Unexpected MQTT disconnection. Will auto-reconnect")

        self._mqtt_client = mqtt.Client(self._clientid)
        self._mqtt_client.will_set(self._status_topic, payload=json.dumps(self._create_status_message("offline")), qos=1, retain=False)
        self._mqtt_client.on_connect = on_connect
        self._mqtt_client.on_disconnect = on_disconnect
        self._mqtt_client.connect_async(self._host, self._port, 60)
        self._mqtt_client.loop_start()

    def _uninit_mqttclient(self):
        self._logger.info("Disconnecting MQTT")
        if self._mqtt_client is None:
            return
        self._mqtt_client.publish(topic=self._status_topic, payload=json.dumps(self._create_status_message("offline")), qos=1, retain=False)
        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()
        self._mqtt_client = None

    def _submit(self, data):
        if self._mqtt_client is None:
            raise Exception("Client not initialized. Call initialize() before submitting data")
        payload = json.dumps(data)
        self._logger.debug("Submitting value '%s' to '%s'", payload, self._data_topic)
        self._mqtt_client.publish(topic=self._data_topic, payload=payload, qos=1, retain=False)

    def _create_status_message(self, status_text):
        return {
            "status": status_text,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }

    def on_next(self, value):
        self._submit(value)

    def on_completed(self):
        pass

    def on_error(self, error):
        self._logger.info("Observer error received: %s", error)

if __name__ == "__main__":
    # only for testing
    import time
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")

    observer = MQTTSink(clientid="mqttsink_test", topic_prefix="mqttsink_test")
    observer.initialize()
    observer.heartbeat()

    observer.on_next({"sensor": "sensor1", "value": 1000})
    observer.on_next({"sensor": "sensor1", "value": 1000})
    observer.on_completed()
    observer.on_error("Something went wrong")
    observer.heartbeat()

    time.sleep(3)
    observer.stop()
