**WORK IN PROGRESS**

# Carberry - IoT - PoC to collect data from a vehicle

Idea: Collect and transfer data from a vehicle using cheap consumer electronics and standard technologies.

Motivation: Proof concept and getting in touch with new technologies and concepts.

Used technologies:
* OBD2
* GPS
* MQTT
* AWS (IoT Core, ...)

Used hardware:
* Raspberry Pi 3
* Huawei e3372 LTE USB Stick
* Exza HHOBD Bluetooth Dongle (ELM327 compatible)
* [GPS Receiver]

Used software: 
* Vehicle
    * Raspberry Pi 3 with jessie
    * Python 3.4.2
        * [paho-mqtt](https://pypi.python.org/pypi/paho-mqtt/1.3.1)
        * [RxPy](https://github.com/ReactiveX/RxPY)
        * [Python obd](http://python-obd.readthedocs.io/en/latest/)
        * [TBD: Python GPS module]
    * [Mosquitto (MQTT broker)](https://mosquitto.org/)
* Stationary
    * AWS IoT Core, Rules
    * AWS Firehose
    * ...

## Architecture - Overview

Data is collected on the vehicle, using an OBD2 Bluetooth Dongle, a GPS USB Dongle and an LTE USB Stick to connect to the internet. All devices are managed by a Raspberry Pi 3, running Python 3 and mosquitto as MQTT broker.

To close the gap to the stationary side, a bridge in Mosquitto is configured, which transfers the data to AWS IoT Core. In AWS the data is streamed to AWS S3 via AWS Kinesis Firehose.

Further processing is done in AWS using AWS Athena and AWS Quicksight. 

General constraints:
* Secure communication from the vehicle to the stationary side (MQTT secured via X509 certificates)
* No vendor specific protocols between vehicle and stationary side, to keep both sides exchangeable
    * Consequence: Use AWS IoT Core, WITHOUT using the Thing Shadows functionalities of AWS
* Use a well known structured data format for data exchange (JSON)
* Buffer messages on the vehicle side, when the internet connection is down
* ...

![Overview](diagrams/overview.png "Overview")

## Carberry Application

### What does it do?

Basic functionality:
* The application is reading the connected OBD2 adapter on a configurable interval, for a configurable list of OBD2 values and submits the data to the locally installed MQTT Broker (mosquitto)
* The application is reading the connected GPS receiver on a configurable interval for the current GPS position and submits the data to the locally installed MQTT Broker
* On a configurable interval the application submits a heartbeat message to the local broker
* the application submits a "online" status message when its connected to the local broker and via MQTT's Last Will and Testament feature an "offline" status 

### How does it work?

#### OBD2 
The application is using the [Python obd](http://python-obd.readthedocs.io/en/latest/) internally, to read data from OBD2. The Pyton obd library is automatically searching for a proper serial device to connect to. Because of this there is no configuration for a serial device required.

The Python obd library is using Pint's Quantity implementation for most return values. The Carberry application extracts value and unit if a Pint Quantity is returned from Pyton obd, otherwise the values returned by the Python obd library are currently just converted to their string representation. 

### Configuration

The configuration can be found in the file `config.json`. 

A description of the configuration (represented as Pyhton data structure) can be found in the file `main.py` searching for the variable `DEFAULT_CONFIGURATION`. This configuration will also be applied by default, if the `config.json` can't be read for some reason.

The application logs the current configuration it is using during startup.

## Carberry - Setting Up Raspberry Pi 3

See [Setup](SETUP.md)

## Carberry - API

See [API](API.md)

## Carberry - Create the foundation for Reporting and Analytics of the Data in AWS

See[AWS Analytics](AWSAnalytics.md)

## What's missing?

* Submitting configuration changes from the stationary side (e.g. change polling intervals, sensors to read)
* Software updates on the Raspberry Pi 3

## Misc

### MQTT on MacOS
Install mosquitto via Homebrew: `brew install mosquitto`

Run locally installed mosquitto: `/usr/local/sbin/mosquitto -c /usr/local/etc/mosquitto/mosquitto.conf`

Listen for all messages: ``mosquitto_sub -t "#"``

### Drawings

https://www.draw.io/

### Commands

Tunnel/SOCKS Proxy via ssh: `ssh -D 3333 user@host`

Create requirements list for Python: `pip3 freeze > requirements.txt`

### WIFI on Raspberry Pi 3

Edit `wpa_supplicant.conf` via `sudo nano /etc/wpa_supplicant/wpa_supplicant.conf` and add your settings:
```
network={
    ssid="NetworkName"
    psk="YourSecretPassword"
}
```