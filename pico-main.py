import machine
import time
from time import sleep
import network
from umqtt.simple import MQTTClient
from machine import Pin, I2C
from imu import MPU6050
import vector3d

print("Imports Successful")

# This section deals with connecting to the local network
def connect(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while wlan.isconnected() == False:
        print("Waiting for connection...")
        time.sleep(1)
    print(wlan.ifconfig())
    
try:
    ssid, password = "LadiesOnSegways-2GHz", "fabdad5000"
    connect(ssid, password)   
except KeyboardInterrupt:
    pass



# This section of code deals with connecting to the MQTT broker
mqtt_server = 'broker.hivemq.com'
client_id = 'xofox'
topic = b'xofox/barbell/left'
message = b'This is a test'

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


# This code sets up out sensor data
i2c = I2C(1, sda=Pin(10), scl=Pin(11), freq=400000)
print(i2c)
imu = MPU6050(i2c)

# Below is the function that will check for new values from the IMU
def IMUValues():
    ax=round(imu.accel.x,2)
    ay=round(imu.accel.y,2)
    az=round(imu.accel.z,2)
    gx=round(imu.gyro.x)
    gy=round(imu.gyro.y)
    gz=round(imu.gyro.z)
    return ax, ay, az, gx, gy, gz

# Below is the code that will be used to calibrate the bar

def calibrate_IMU(iterations):
   ax, ay, az, gx, gy, gz = [], [], [], [], [], []


# Below is the main loop
while True:
    ax, ay, az, gx, gy, gz = IMUValues()
    tem=round(imu.temperature,2)
    print("ax",ax,"\t","ay",ay,"\t","az",az,"\t","gx",gx,"\t","gy",gy,"\t","gz",gz,"\t","Temperature",tem,"        ",end="\r")
    imuMessage = f"aX = {ax}, \t aY = {ay}, \t aZ = {az}, \t gX = {gx}, \t gY = {gy}, \t gZ = {gz} \t"
    client.publish(topic, imuMessage)
    sleep(0.1)


