# Carberry - Setting Up Raspberry Pi 3

The following document describes how to setup a Raspberry Pi 3.

## Install Huawei e3372 LTE Stick

Hint: The USB Stick i'm using is running with the Huawei HiLink firmware, which connects via eth1 and not as regular USB modem. This means there is some kind of NATting involved via the stick and the device (the stick is connected to) is getting an IP from a private range (192.168.x.x) and not directly the IP address assigned by the network operator. This is not an issue for my current setup, as i'm only using outgoing connection. 

By default the stick is recognized as usb-storage device and has to be switched to Modem mode, each time the Raspberry was powered off.

Manually switch to modem mode: `sudo usb_modeswitch -v 12d1 -p 1f01 -M '55534243123456780000000000000a11062000000000000100000000000000'`

To automatically switch the stick to Modem mode, add: 
```
ATTRS{idVendor}=="12d1", ATTRS{idProduct}=="1f01", RUN+="/usr/sbin/usb_modeswitch -v 12d1 -p 1f01 -M '55534243123456780000000000000a11062000000000000100000000000000'"
```
to the file `/lib/udev/rules.d/40-usb_modeswitch.rules`.

## Install GPS Module

The GPS Module will be connect via serial port (connect to GPIO14 / GPIO15 of the Raspberry Pi 3 header).

On the Raspberry 3 Pi by default the UART0 is used for the internal Bluetooth module and can not be used for the serial port (on the header).

So some steps have to be done, to configure the serial port properly:
1. Enable serial port and disable serial console via `raspi-config`
2. Remove `console=serial0,115200` from `/boot/cmdline.txt`
3. Add the following lines to the end of `/boot/config.txt`
```
dtoverlay=pi3-miniuart-bt
enable_uart=1
core_freq=250
```
4. Restart Raspberry

Details about reconfiguring the serial ports can be found here: https://wiki.fhem.de/wiki/Raspberry_Pi_3:_GPIO-Port_Module_und_Bluetooth

After the serial ports are setup properly, follow these steps to setup the GPS Module:
1. Install the required GPS packages: `sudo apt-get install gpsd gpsd-clients`
2. Check whether GPS data available via serial port: `cat /dev/ttyAMA0``
3. To configure gpsd to use the proper serial port run `sudo nano /etc/default/gpsd`and a change `DEVICES=""` to `DEVICES="/dev/ttyAMA0"`
4. Run `cgps` to check if the GPS Module is working.

## Connect OBD2 Bluetooth Dongle

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

## Test OBD2 Bluetooth Dongle

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

## Install MQTT Broker Mosquitto

Run the following command to install Mosquitto: `sudo apt-get install -y mosquitto mosquitto-clients`

After the installation the MQTT broker should be running.

To validate, if mosquitto is running execute `mosquitto_sub -t "#"` in one terminal to subscribe to all topics. And in another terminal run `mosquitto_pub -t "greetings" -m "hello"`. After publishing the message `hello`should appear in the first terminal.

Update the persistence settings in Mosquitto's config file `/etc/mosquitto/mosquitto.conf` according to your needs. As by default Mosquitto only persists its subscription / messages etc. when exiting, data may be lost when the Raspberry Pi 3 is "switched off" (e.g. when connected via 12V USB adapter which will be switched of when you leave your car).
For example add the line `autosave_interval 60` to automatically persist data to disk every 60 seconds.

UPDATE: It looks like Raspian jessie references a very old version of mosquitto, which does not support the latest MQTT protocol (3.1.1) required for AWS IoT. 
So an update is required, see description at http://agilerule.blogspot.de/2016/05/install-mqtt-mosquitto-on-raspberry-pi.html.

Steps:
1. `sudo wget http://repo.mosquitto.org/debian/mosquitto-repo.gpg.key`
2. `sudo apt-key add mosquitto-repo.gpg.key`
3. `cd /etc/apt/sources.list.d/`
4. `sudo wget http://repo.mosquitto.org/debian/mosquitto-jessie.list`
5. `sudo apt-get update`
6. `sudo apt-get install mosquitto mosquitto-clients`

## Bridge mosquitto to AWS IoT Core

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

**Important: If you have multiple instances of Carberry installations, the `clientid` used in the bridge configuration has to be different! As AWS will disconnect other clients if they are using the same clientid!**

## Install Carberry application software

### Installation steps

1. Install Python3: `sudo apt-get install python3 python3-pip`
2. Install git: `sudo apt-get install git`
3. Change directory: `cd /opt`
4. Clone this repository: `git clone https://github.com/mtiews/carberry.git`
5. Change into cloned directory: `cd carberry`
6. Install required Python libraries: `sudo pip3 install -r requirements.txt`
7. Check the configuration file `config.json` and change it according to your needs (e.g. change intervals and sensors to read from OBD2)

After these steps the application can be started via `python3 main.py`, to check whether it is working properly. Have a look at your local mosquitto via `mosquitto_sub -t "#"` and check if all data is submitted properly.

### Run Carberry as service using systemd

1. Create a user: `sudo useradd -r -s /bin/false carberry`
2. Add the user to the `dialout` group, to allow accessing the `/dev/rfcomm0` (where the OBD2 Bluetooth Dongle is bind to): `sudo usermod -a -G dialout carberry`
3. Create a config file for systemd: `sudo nano /etc/systemd/system/carberry.service`
4. Paste the following content into the file:
```
[Unit]
Description=Carberry Application Service
After=syslog.target mosquitto.service

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
