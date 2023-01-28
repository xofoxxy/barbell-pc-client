from paho.mqtt import client as mqtt_client

# Now from here we need to initialize all the components that will go into establishing mqtt connection

broker = "broker.hivemq.com"
port = 1883
topic = "xofox/barbell/left"
client_id = "XofoxPC"

messageQueue = 0

# Username =
# Password =

def connect_mqtt():
    # This function constructs the client object, connects it to the MQTT server and then returns it
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id)
    # client.username_pw_set(username=,password=)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client


def subscribe(client: mqtt_client, queue):
    def on_message(client, userdata, msg):
        queue.put(msg.payload.decode())

    client.subscribe(topic)
    client.on_message = on_message


def run(queue):
    client = connect_mqtt()
    subscribe(client, queue)
    client.loop_forever()
