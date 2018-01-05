#!/usr/bin/env python3

import logging
import time
import json

from data_transfer import DataTransfer
from mqtt_sink import MQTTSink
from obd2_adapter import OBD2Adapter
from gps_adapter import GPSAdapter

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(threadName)s - %(name)s - %(levelname)s - %(message)s")
LOGGER = logging.getLogger("CARBERRY")
    
# Configuration values - locally fixed
MQTT_CLIENT_NAME = "carberry"
MQTT_HOST = "localhost"
MQTT_PORT = 1883
MQTT_TOPIC_PREFIX = MQTT_CLIENT_NAME

# DEFAULT configuration will be used, if file "config.json" does not exist
CONFIGURATION_FILE = "config.json"
DEFAULT_CONFIGURATION = {
    "config_info": "Default configuration from source code",
    # General settings - used for class DataTransfer
    "general" : {
        # Interval in seconds
        "heartbeat_interval": 300,
        # Interval in seconds
        "obd2_poll_interval": 60,
        # Interval in seconds
        "gps_poll_interval": 60
    },
    # Settings for OBD2 adapter - used for class OBD2Adapter
    "obd2": {
        "sensors": [ 
            "STATUS",
            "RPM",
            "SPEED"
        ]
    },
    # Settings for GPS adapter - used for class GPSAdapter
    "gps": {
    }
}
# END - DEFAULT Configuration

# Will hold the configuration that is used by the application
CONFIGURATION_IN_USE = None

def parse_and_validate_config_string(config_as_string):
    if config_as_string == None:
        LOGGER.error("Configuration string is empty")
        return None

    parsed_config = None
    try:
        parsed_config = json.loads(config_as_string)
    except Exception as error:
        LOGGER.error("Failed to parse config string: %s , content: %s", error, config_as_string)
        return None

    return parsed_config

if __name__ == "__main__":
    LOGGER.info("Starting module...")

    # Loading configuration from file
    LOGGER.info("Loading configuration file '%s'...", CONFIGURATION_FILE)
    config_string = None
    temp_config = None
    try:
        with open("config.json", "r") as f:
            config_string = f.read()
    except Exception as error:
        LOGGER.error("Config file not found: %s", error)

    # Parse and validate configuration loaded from file
    temp_config = parse_and_validate_config_string(config_string)
    if temp_config == None:
        CONFIGURATION_IN_USE = DEFAULT_CONFIGURATION
        LOGGER.warning("Using default configuration")
    else:
        CONFIGURATION_IN_USE = temp_config

    LOGGER.info("Current configuration: %s", json.dumps(CONFIGURATION_IN_USE, indent=4))

    # Initialize dependencies
    sink = MQTTSink(clientid=MQTT_CLIENT_NAME, topic_prefix=MQTT_TOPIC_PREFIX)
    obd2 = OBD2Adapter(configuration=CONFIGURATION_IN_USE["obd2"])
    gps = GPSAdapter(configuration=CONFIGURATION_IN_USE["gps"])

    # Start data transfer     
    dtrans = DataTransfer(mqtt_sink=sink, obd2_adapter=obd2, gps_adapter=gps)
    dtrans.start(configuration=CONFIGURATION_IN_USE["general"])

    while 1:
        time.sleep(10)

    LOGGER.info("...done")
    