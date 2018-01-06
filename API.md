# Carberry - API

This document describes the external API of the Carberry Application, which exposes its data inputs/outputs ONLY via MQTT!

The application exposes its data to the locally installed MQTT Broker (Mosquitto). Topics mentioned in this 
document refer to the topic names used locally by the Python-based application code when interfacing with the local Mosquitto installation.

Depending on your specific configuration of the MQTT bridge, which mirrors the topics to the stationary side,
the topics on the stationary side may vary.

## Overview

The application exposes its data to the following three topics:

* `carberry/status` - status messages during the application lifecycle
* `carberry/heartbeat` - heartbeat message sent by the application in configurable intervals
* `carberry/data` - usage data like OBD2 sensor values and GPS data will be sent using this topic.

## Status topic - `carberry/status`

Information about the application lifecyle will be sent, using this topic.

Via Last Will and Testament of MQTT a `status="offline"` message will be sent, if the application shuts down or is terminated.

Sample message:
```
{
    "status": "online", 
    "status_text": "Application bootstrapped successfully.", "timestamp": 1515254387767, 
    "timestamp_str": "2018-01-06T15:59:47.767000"
}
```

## Heartbeat topic - `carberry/heartbeat`

Simple heartbeat message sent by the application in configurable intervals.

Sample message:
```
{
    "timestamp": "2018-01-06T16:11:49.462340"
}
```

## Data topic - `carberry/data`

All usage data messages will be sent using this topic.

Messages of this topic contain a `source` field to identify their source / type of message.

### OBD2
```
{
    "source": "obd2",
    "sensor": "RPM",
    "value": 830.5,
    "unit": "revolutions_per_minute",
    "timestamp": 1515255173707,
    "timestamp_str": "2018-01-06T16:12:53.707000",
    "error": null
}
```

### GPS

```
{
    "source": "gps",
    "value": {
        "longitude": 24.24,
        "latitude": 12.12
    },
    "timestamp": 1515255178291,
    "timestamp_str": "2018-01-06T16:12:58.290999",
    "error": null
}
```