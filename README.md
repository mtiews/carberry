**WORK IN PROGRESS**

# IoT - PoC to collect data from a vehicle

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

### Install Huawei e3372 LTE Stick

Hint: The USB Stick i'm using is running with the Huawei HiLink firmware, which connects via eth1 and not as regular USB modem. This means there is some kind of NATting involved via the stick and the device (the stick is connected to) is getting an IP from a private range (192.168.x.x) and not directly the IP address assigned by the network operator. This is not an issue for my current setup, as i'm only using outgoing connection. 

By default the stick is recognized as usb-storage device and has to be switched to Modem mode, each time the Raspberry was powered off.

Manually switch to modem mode: `sudo usb_modeswitch -v 12d1 -p 1f01 -M '55534243123456780000000000000a11062000000000000100000000000000'`

To automatically switch the stick to Modem mode, add: 
```
ATTRS{idVendor}=="12d1", ATTRS{idProduct}=="1f01", RUN+="/usr/sbin/usb_modeswitch -v 12d1 -p 1f01 -M '55534243123456780000000000000a11062000000000000100000000000000'"
```
to the file `/lib/udev/rules.d/40-usb_modeswitch.rules`.

### Connect OBD2 Bluetooth Dongle

Start `bluetoothctl`, and enter the following commands:
1. agent on
2. pairable on
3. scan on
*Wait until Bluetooth Adapter has been found*
4. pair [MAC-Adresse]
*Wait for PIN prompt*
5. trust [MAC-Adresse]
6. connect [MAC-Adresse]
*After that you should see a NotAvailable error message*
7. info [MAC-Adresse]
Will display a `connected: no`

Using the previous steps, should automatically reconnect the Bluetooth Dongle after reboot.

Now the serial port can be configured: (https://bbs.archlinux.org/viewtopic.php?id=178011):
1. `sudo modprobe rfcomm`
2. `sudo rfcomm bind rfcomm0 [MAC-Adresse]`
3. `ls /dev |grep rfcomm` should display `rfcomm0`

Add the following line to `/etc/rc.local`:
```
`sudo rfcomm bind rfcomm0 [MAC-Adresse] &`
```
to enable the serial port automatically during startup.
Not nice, but all other solutions didn't work. :-(

Add

### Test OBD2 Bluetooth Dongle

Install screen `sudo apt-get install screen`
Run `screen /dev/rfcomm0` to communicate with the OBD2 Adapter

Run the following sequence in screen:

`ATZ`
Restarts the device. You’ll need to do this from time to time.

`ATL1`
Turns linefeeds on

`ATH1`
Turns headers on

`ATS1`
Turns spaces on

`ATSP0`
Set the protocol to Auto

`ATI` 
Show information about the device (ELM 327 plus version information)

`03`
Shows the current error codes

You can press CTRL+A, CTRL+D to exit screen

Detailed information about OBD-II can be found at Wikipedia: https://en.wikipedia.org/wiki/OBD-II_PIDs

The ELM327 can speak **CAN** as well, but that's another story. 

### Install MQTT Broker Mosquitto

Run the following command to install Mosquitto: `sudo apt-get install -y mosquitto mosquitto-clients`

After the installation the MQTT broker should be running.

To validate, if mosquitto is running execute `mosquitto_sub -t "#"` in one terminal to subscribe to all topics. And in another terminal run `mosquitto_pub -t "greetings" -m "hello"`. After publishing the message `hello`should appear in the first terminal.

UPDATE: It looks like Raspian jessie references a very old version of mosquitto, which does not support the latest MQTT protocol (3.1.1) required for AWS IoT. 
So an update is required, see description at http://agilerule.blogspot.de/2016/05/install-mqtt-mosquitto-on-raspberry-pi.html.

Steps:
1. `sudo wget http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key`
2. `sudo apt-key add mosquitto-repo.gpg.key`
3. `cd /etc/apt/sources.list.d/`
4. `sudo wget http://repo.mosquitto.org/debian/mosquitto-jessie.list`
5. `sudo apt-get update`
6. `sudo apt-get install mosquitto mosquitto-clients`

### Bridge mosquitto to AWS IoT Core

A detailed description can be found here: https://aws.amazon.com/de/blogs/iot/how-to-bridge-mosquitto-mqtt-broker-to-aws-iot/

The basic steps are:
1. In AWS IoT create a Thing with certificate and keys, attach a policy to allow the Thing to connect and publish to AWS IoT.
2. Download certificate and keys (incl. Root Certificate) and copy them to the Raspberry Pi.
3. Ensure, that in AWS IoT the certificate is activated (by default the certifcates are deactivated after initial creation)
4. Create a Mosquitto bridge configuration `/etc/mosquitto/conf.d/bridge.conf`, like so:
```
# AWS IoT endpoint, use AWS CLI 'aws iot describe-endpoint'
connection awsiot
address XXXXXXXXXX.iot.eu-central-1.amazonaws.com:8883

# map local carberry to source specific topic in AWS IoT
topic # out 1 carberry/ carberry/passat/

# Setting protocol version explicitly
bridge_protocol_version mqttv311
bridge_insecure false

# Bridge connection name and MQTT client Id,
# enabling the connection automatically when the broker starts.
cleansession true
clientid cbpassat
start_type automatic
notifications false
log_type all

#Path to the rootCA, Certificate and Private key
bridge_cafile /etc/mosquitto/certs/rootCA.crt
bridge_certfile /etc/mosquitto/certs/certificate.pem.crt
bridge_keyfile /etc/mosquitto/certs/private.pem.key
```

### Install Carberry application software

#### Installation steps

1. Install Python3: `sudo apt-get install python3 python3-pip`
2. Install git: `sudo apt-get install git`
3. Change directory: `cd /opt`
3. Clone this repository: `git clone https://github.com/mtiews/carberry.git`
4. Change into cloned directory: `cd carberry`
5. Install required Python libraries: `sudo pip3 install -r requirements.txt`
6. Check the configuration file `config.json` and change it according to your needs (e.g. change intervals and sensors to read from OBD2)

After these steps the application can be started via `python3 main.py`, to check whether it is working properly. Have a look at your local mosquitto via `mosquitto_sub -t "#"` and check if all data is submitted properly.

#### Run Carberry as service using systemd

1. Create a user: `sudo useradd -r -s /bin/false carberry`
2. Add the user to the `dialout` group, to allow accessing the `/dev/rfcomm0` (where the OBD2 Bluetooth Dongle is bind to): `sudo usermod -a -G dialout carberry`
2. Create a config file for systemd: `sudo nano /etc/systemd/system/carberry.service`
3. Paste the following content into the file:
```
[Unit]
Description=Carberry Application Service
After=syslog.target

[Service]
Type=simple
User=carberry
Group=carberry
WorkingDirectory=/opt/carberry
ExecStart=/opt/carberry/main.py
SyslogIdentifier=carberry
StandardOutput=syslog
StandardError=syslog
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
4. Reload systemd configuration: `sudo systemctl daemon-reload`
5. Enable service: `sudo systemctl enable carberry.service`

Log outputs are written to `/var/log/syslog`.

To view the logs run `sudo journalctl -u carberry` or `sudo journalctl -f -u carberry` to follow the logs.

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