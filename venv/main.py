import matplotlib;

matplotlib.use("TkAgg")
import multiprocessing
import numpy as np
from scipy.spatial.transform import Rotation
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import threading
import datetime
import firebase_admin as firebase
from firebase_admin import credentials
from firebase_admin import firestore
import keyboard
from filterpy.kalman import KalmanFilter
import helperFunctions

dataInputQueue = multiprocessing.Queue()
dataInputQueue = multiprocessing.Queue()
cred_obj = firebase.credentials.Certificate(
    r"C:\Users\sethl\PycharmProjects\barbell PC client\barbarix-app-firebase-adminsdk-qymun-9671e7cdc1.json")
default_app = firebase.initialize_app(cred_obj)
firebase_db = firestore.client()
firebase_db_ref = firebase_db.collection(u'barbells').document(u"barbell4")

meanAX = 0
meanAY = 0
meanAZ = 0
meanW = 0
meanX = 0
meanY = 0
meanZ = 0
weightIDs = []
weight = 45


# This function counts the total amount of weight according to weight ID numbers and then returns that number.

def calculateWeight(weightList):
    print(weightList)
    return 45


# Because we know that the mqtt data is going to be coming in the format of:
# Accelerometer data (X,Y,Z), Euler Angles (Heading, Pitch, Roll), and then calibration data (System, Gyroscope, Accelerometer
# Magnetometer) followed by the IDs of the weights that it's detected, we need to make sure that the PC client expects that.

# This function does the following:
# First, it pulls in the data from the queue
# Second, it splits it along the commas
# 3rd it converts the weight IDs into an actual weight amount
# 4th it factors in the averages for the sensor data
# 5th it appends the data into the dataframe and then returns the data as well

def pull_from_queue(dataset, inputQueue):
    global meanAX, meanAY, meanAZ, meanH, meanP, meanR
    global weightIDs
    global weight
    string = inputQueue.get()
    string = string.replace('(', '').replace(')', '')
    stringList = string.split(',')

    aX, aY, aZ, w, x, y, z, sC, gC, aC, mC = [stringList[i] for i in range(0, 11)]
    if sC == 0 or gC == 0 or aC == 0 or mC == 0:
        return

    # This function will adjust the values for the
    aX, aY, aZ = helperFunctions.adjust_for_spin(aX, aY, aZ, w, x, y, z)
    # Here is where we're going to handle for the weight IDs. If more than 10 parameters are passed, we know that there
    # are IDs that need to be handled.
    if len(stringList) > 10:
        weightIDs.append([stringList[i] for i in range(11, len(stringList))])

    if not weightIDs:
        weight = calculateWeight(weightIDs)

    # TODO: we need to actually make the script handle for the IDs now that we have them collected. In order to do that

    dataset.loc[datetime.datetime.now()] = [float(aX) - meanAX, float(aY) - meanAY, float(aZ) - meanAZ,
                                            float(w) - meanW,
                                            float(x) - meanX,
                                            float(y) - meanY,
                                            float(z) - meanZ, int(sC), int(gC), int(aC), int(mC), float(weight)]
    return float(aX) - meanAX, float(aY) - meanAY, float(aZ) - meanAZ, float(w) - meanW, float(x) - meanX, float(
        y) - meanY, float(z) - meanZ, int(sC), int(gC), int(aC), int(mC), float(weight)


# This function will take the amount that the sensor has rotated and rotate its results by that same amount so that
# the results are always in line with each other and completely comparable.
# Heading is rotation about X
# Pitch is rotation about Y
# Roll is rotation about Z


# TODO: finish all of the score calculations
def calculate_momentum(aX, aY, aZ, w, x, y, z, sC, gC, aC, mC, weight):
    return 'NA'


def calculate_effort(aX, aY, aZ, w, x, y, z, sC, gC, aC, mC, weight):
    return 'NA'


def calculate_stability(aX, aY, aZ, w, x, y, z, sC, gC, aC, mC, weight):
    return 'NA'


def findAverages(dataset, inputQueue, sampleSize):
    global meanAX, meanAY, meanAZ, meanGX, meanGY, meanGZ

    while len(dataset) < sampleSize:
        pull_from_queue(dataset, inputQueue)
    print(f"{sampleSize} Samples have been collected")
    print("These are the averages: \n")
    meanAX = dataset["aX"].mean()
    meanAY = dataset["aY"].mean()
    meanAZ = dataset["aZ"].mean()
    meanW = dataset['quatW'].mean()
    meanX = dataset["quatX"].mean()
    meanY = dataset["quatY"].mean()
    meanZ = dataset["quatZ"].mean()
    print(meanAX, meanAY, meanAZ, meanW, meanX, meanY, meanZ)


def trailing_average(database, index, n):
    sum = 0
    for i in range(0, n):
        sum += database[index][-i]
    pass
    return sum/n


# Thread 1 is going to be used solely for listening in onto the MQTT channel and putting data into the queue.
# The first parameter is the queue that we want the data to flow into.
def thread_1_startMQTT(inputQueue):
    print("Thread 1 has begun")
    import mqtt
    mqtt.run(inputQueue)


def liveGraph(i, x1, y1, y2, y3, y4, y5, y6, database1, database2):
    # here we attempt to assign all the left-side graph values

    try:
        y1.append(trailing_average(database1, "aX", 5))
        y2.append(trailing_average(database1, "aY", 5))
        y3.append(trailing_average(database1, "aZ", 5))
        # x1 needs to be appended to after the others since the others will raise an error until the other threads
        # have begun, and we need the lists to have the same dimensions
        x1.append(datetime.datetime.now())
    except IndexError:
        return

    # Here we attempt to assign all the right-side graph values
    #     y4.append(database2['aX'][-1])
    #     y5.append(database2['aY'][-1])
    #     y6.append(database2['aZ'][-1])
    #     # x1 needs to be appended to after the others since the others will raise an error until the other threads
    #     # have begun, and we need the lists to have the same dimensions
    # except:
    #     return

    x1 = x1[-5:]
    y1 = y1[-5:]
    y2 = y2[-5:]
    y3 = y3[-5:]

    ax1.clear()
    ax2.clear()
    ax3.clear()
    ax1.plot(xs, ys1)
    ax2.plot(xs, ys2)
    ax3.plot(xs, ys3)
    # ax1.plot(xs, ys4)
    # ax2.plot(xs, ys5)
    # ax3.plot(xs, ys6)

    # Format plot
    plt.xticks(rotation=45, ha='right')
    plt.subplots_adjust(bottom=0.30)
    ax1.set_title('X Acceleration')
    ax2.set_title('Y Acceleration')
    ax3.set_title('Z Acceleration')


# Thread 2 is going to be used for doing the initial processing of the data
# The first parameter is the queue that we want the data to flow out of, or in other words the data
# that we want to be processing.
def thread_2_processing(inputQueue, outboxQueue):
    global weight, fig
    print("Thread 2 has begun")

    # findAverages(movement_database, inputQueue, 30)

    # This should empty the queue so that we can start fresh now that we have our averages
    # while not inputQueue.empty():
    #     inputQueue.get()
    #     print(inputQueue.qsize())

    print("Main processing Loop has begun!")
    while True:

        if not inputQueue.empty():
            aX, aY, aZ, w, x, y, z, sC, gC, aC, mC, weight = pull_from_queue(movement_database_left, inputQueue)

            scores = []
            # Right now the keyboard interaction simulates a rep happening Todo: Make this reps instead of the A key
            #  we want the actual scores to be 0 unless a rep has happened so that we have some way for thread 3 to
            #  detect new reps
            if keyboard.is_pressed('a'):
                print("A key has been pressed!")
                momentum = calculate_momentum(aX, aY, aZ, w, x, y, z, sC, gC, aC, mC, weight)
                effort = calculate_effort(aX, aY, aZ, w, x, y, z, sC, gC, aC, mC, weight)
                stability = calculate_stability(aX, aY, aZ, w, x, y, z, sC, gC, aC, mC, weight)
                scores = [effort, momentum, stability, sC, gC, aC, mC]
            else:
                scores = [0, 0, 0, sC, gC, aC, mC]

            outboxQueue.put(scores)


# Thread 3 will be designated to handling pushing things to the website and making sure that everything on the website
# gets managed. Any feedback from the website will go into the inbox and anything that needs to be sent to the database
# will be put into the outbox by other functions.
def thread_3_firestore(inbox, outbox):
    print("thread 3 has begun")
    # First we need to be checking to see if there's any new scores to put up as a rep
    while True:
        if not outbox.empty():
            scores = outbox.get()

            if scores[0] != 0:
                print("Assembling array!")

                repArray = [
                    {'effort': scores[0], 'momentum': scores[1], 'time': datetime.datetime.now(), 'type': scores[2]}]
                firebase_format = {
                    'name': 'barbell4',
                    'active': scores[3],
                    'gyroscope': scores[4],
                    'accelerometer': scores[5],
                    'magnetometer': scores[6],
                    'reps': firestore.ArrayUnion(repArray)
                }
                firebase_db_ref.set(firebase_format, merge=True)
                print("Array has been pushed!")

    pass


# First we declare all of the things that we're going to use frequently in the main processing loop, and it's helper
# functions
movement_database_left = pd.DataFrame(columns=['aX', 'aY', 'aZ', 'quatW', 'quatX', 'quatY', 'quatZ', 'systemStatus',
                                               'gyroStatus', 'accelStatus', 'magStatus', 'weight'])
movement_database_right = pd.DataFrame(columns=['aX', 'aY', 'aZ', 'quatW', 'quatX', 'quatY', 'quatZ', 'systemStatus',
                                                'gyroStatus', 'accelStatus', 'magStatus', 'weight'])

# This queue will be used to have multiple threads running at once and will store the messages coming from MQTT
messageQueue = multiprocessing.Queue()
inboxQueue = multiprocessing.Queue()
outboxQueue = multiprocessing.Queue()

# Here we'll assign which threads will manage which loops
thread1 = threading.Thread(target=thread_1_startMQTT, args=(dataInputQueue,))
thread2 = threading.Thread(target=thread_2_processing, args=(dataInputQueue, outboxQueue,))
thread3 = threading.Thread(target=thread_3_firestore, args=(inboxQueue, outboxQueue,))
thread1.start()
thread2.start()
thread3.start()

# The animation stuff needs to be running on the main thread and so we'll start that up once the others have
# begun. this is all stuff that needs to be initialized so that the live graphing works and looks good here we change
# the style
style.use("fivethirtyeight")

# here we create the figure object
fig, (ax1, ax2, ax3) = plt.subplots(3, 1, sharex=True, sharey=False)

# Here we create the lists that the graph will be pulling from
xs = []
ys1 = []
ys2 = []
ys3 = []
ys4 = []
ys5 = []
ys6 = []

# this animation call has to be running on the main thread because matplotlib isn't threadsafe.
ani = animation.FuncAnimation(fig, liveGraph, frames=100,
                              fargs=(xs, ys1, ys2, ys3, ys4, ys5, ys6, movement_database_left, movement_database_right),
                              interval=50)
plt.show()

# Todo: update the pico so that it updates more frequently
