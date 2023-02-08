import multiprocessing
import numpy as np
import regex
import pandas as pd
from scipy.spatial.transform import Rotation
import matplotlib
import threading
import time
import datetime
import firebase_admin as firebase
from firebase_admin import credentials
from firebase_admin import firestore

dataInputQueue = multiprocessing.Queue()

meanAX = 0
meanAY = 0
meanAZ = 0
meanGX = 0
meanGY = 0
meanGZ = 0


# The purpose of this function is to find the average of a set of data and then simplify the data down to its averages.
def pull_from_queue(dataset, inputQueue):
    # We need to pull in our means so that whenever we decide to change our calibration data the new entries will
    # automatically be calibrated.
    global meanAX, meanAY, meanAZ, meanGX, meanGY, meanGZ

    # We first declare the regex that all of the messages in the queue should be following
    message_format = regex.compile("aX = ([+-]?\d*.\d*), \t aY = ([+-]?\d*.\d*), \t aZ = ([+-]?\d*.\d*), \t gX = (["
                                   "+-]?\d*.\d*), \t gY = ([+-]?\d*.\d*), \t gZ = ([+-]?\d*.\d*)")

    string = inputQueue.get()
    regexList = message_format.split(string)
    aX, aY, aZ, gX, gY, gZ = [regexList[i] for i in range(1, 7)]
    dataset.loc[datetime.datetime.now()] = [float(aX) - meanAX, float(aY) - meanAY, float(aZ) - meanAZ,  
                                            float(gX) - meanGX, float(gY) - meanGY,
                                            float(gZ) - meanGZ, 0, 0, 0, 0, 0, 0]
    return float(aX) - meanAX, float(aY) - meanAY, float(aZ) - meanAZ, float(gX) - meanGX, float(
        gY) - meanGY, float(
        gZ) - meanGZ


# This function in theory should convert the gyro data into angular data the way that we can do that is by assuming that
# we start at 0 degrees on every axis and then convert the rotational inertia to angular change. By keeping track of the
# angular change we can estimate our absolute angle


# The purpose of this portion is to take in the rotation and adjust the accelerometer data according to the gyro data


def findAverages(dataset, inputQueue, sampleSize):
    global meanAX, meanAY, meanAZ, meanGX, meanGY, meanGZ

    while len(dataset) < sampleSize:
        pull_from_queue(dataset, inputQueue)
    print(f"{sampleSize} Samples have been collected")
    print("These are the averages: \n")
    meanAX = dataset["aX"].mean()
    meanAY = dataset["aY"].mean()
    meanAZ = dataset["aZ"].mean()
    meanGX = dataset["gX"].mean()
    meanGY = dataset["gY"].mean()
    meanGZ = dataset["gZ"].mean()
    print(meanAX, meanAY, meanAZ, meanGX, meanGY, meanGZ)


# Thread 1 is going to be used solely for listening in onto the MQTT channel and putting data into the queue.
# The first parameter is the queue that we want the data to flow into.
def thread_1_startMQTT(inputQueue):
    print("Thread 1 has begun")
    import mqtt
    mqtt.run(inputQueue)


# Thread 2 is going to be used for doing the initial processing of the data
# The first parameter is the queue that we want the data to flow out of, or in other words the data
# that we want to be processing.
def thread_2_processing(inputQueue):
    print("Thread 2 has begun")

    # First we declare all of the things that we're going to use frequently in the main processing loop
    movement_database = pd.DataFrame(columns=['aX', 'aY', 'aZ', 'gX', 'gY', 'gZ', 'pX', 'pY', 'pZ', 'yaw', 'pitch',
                                              'roll'])

    findAverages(movement_database, inputQueue, 30)

    # This should empty the queue so that we can start fresh now that we have our averages
    while not inputQueue.empty():
        inputQueue.get()
        print(inputQueue.qsize())

    print("Main processing Loop has begun!")
    while True:
        # TODO: First, we need to take each data point and apply the rotational
        # transformation onto it to have it be aligned with everything else
        # TODO: Once we have all the raw data, that stuff needs to be put into the queue to be sent to the server

        if not inputQueue.empty():
            aX, aY, aZ, gX, gY, gZ = pull_from_queue(movement_database, inputQueue)
            # print(f"\r{aX}, {aY}, {aZ}, {gX}, {gY}, {gZ}")


# Thread 3 will be designated to handling pushing things to the website and making sure that everything on the website
# gets managed. Any feedback from the website will go into the inbox and anything that needs to be sent to the database
# will be put into the outbox by other functions.
def thread_3_firestore(inbox, outbox):
    pass


# This queue will be used to have multiple threads running at once and will store the messages coming from MQTT
messageQueue = multiprocessing.Queue()
inboxQueue = multiprocessing.Queue()
outboxQueue = multiprocessing.Queue()

# Here we'll assign which threads will manage which loops
thread1 = threading.Thread(target=thread_1_startMQTT, args=(dataInputQueue,))
thread2 = threading.Thread(target=thread_2_processing, args=(dataInputQueue,))
thread1.start()
thread2.start()
# this is a change
