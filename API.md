# Carberry - API

This document describes the external API of the Carberry Application, which exposes its data inputs/outputs ONLY via MQTT!

The application exposes its data to the locally installed MQTT Broker (Mosquitto). Topics mentioned in this 
document refer to the topic names used locally by the Python-based application code when interfacing with the local Mosquitto installation.

Depending on your specific configuration of the MQTT bridge, which mirrors the topics to the stationary side,
the topics on the stationary side may vary.

## Overview

The application exposes its data to the following three topics:

* `carberry/status` - status messages during the application lifecycle
* `carberry/data` - usage data like OBD2 sensor values and GPS data will be sent using this topic.

## Status topic - `carberry/status`

Information about the application lifecyle will be sent, using this topic.

Via Last Will and Testament of MQTT a `status="offline"` message will be sent, if the application shuts down or is terminated.

Sample message:
```
{
    "status": "online", 
    "status_text": "Application bootstrapped successfully.", 
    "timestamp": 1515254387767, 
    "timestamp_str": "2018-01-06T15:59:47.767000"
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

The gps `value` reflects the record type TPV documented here: http://www.catb.org/gpsd/gpsd_json.html 

```
{
    "source": "gps",
    "timestamp_str": "2018-01-12T22:07:21.786000", 
    "timestamp": 1515794841786,
    "value": {
        "track": 0.0, 
        "epv": 25.3, 
        "epy": 12.6, 
        "alt": 319.4, 
        "epx": 9.7, 
        "tag": "GBS", 
        "time": "2018-01-12T22:07:21.000Z", 
        "epd": "n/a", 
        "device": "/dev/ttyAMA0", 
        "lat": 48.000000, 
        "climb": 0.0, 
        "eps": 27.41, 
        "speed": 0.137, 
        "lon": 11.000000, 
        "ept": 0.005, 
        "mode": 3, 
        "epc": "n/a"
    }, 
}
```