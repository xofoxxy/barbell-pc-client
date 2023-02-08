import machine
import time
from bno055 import *
import network
from umqtt.simple import MQTTClient

print("Imports Successful")
# Pyboard hardware I2C
i2c = machine.I2C(0,scl=machine.Pin(13), sda=machine.Pin(12))
imu = BNO055(i2c)
calibrated = False
# First step that we need to do now that we have all of the i2c set up is to initialize the mqtt transferring

# This section deals with connecting to the local network
def connect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print("Waiting for connection...")
        time.sleep(1)
    print(wlan.ifconfig())
    

ssid, password = "Ladiesonsegways", "fabdad5000"
connect(ssid, password)   


# This here is all information for the mqtt service and the portion of code following it deals with connecting to that
mqtt_server = 'broker.hivemq.com'
client_id = 'xofox'
topic = b'xofox/barbell/left'


# This all will just keep looping until the board sucessfully connects to the mqtt broker
def mqtt_connect():
    client = MQTTClient(client_id, mqtt_server, keepalive = 120)
    client.connect()
    print(f'Connected to {mqtt_server}\'s MQTT broker')
    return client

connected = False

while connected == False:   
    try:
        client = mqtt_connect()
        print(client)
        connected = True
    except:
        connected = False 


def IMUValues():
    ax, ay, az = imu.accel() # accelerometer data
    h, r, p = imu.euler() # Heading, Roll, Pitch
    sc, gc, ac, mc = imu.cal_status() # Calibration statuses
    return ax, ay, az, h, r, p, sc, gc, ac, mc


while True:
    time.sleep(1)
    print(IMUValues())
    client.publish(topic, str(IMUValues()))