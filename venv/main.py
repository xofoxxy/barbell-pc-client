import multiprocessing
import numpy as np
import regex
import pandas as pd
from scipy.spatial.transform import Rotation
import matplotlib
import threading
import datetime
import firebase_admin as firebase
from firebase_admin import credentials
from firebase_admin import firestore
import keyboard

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
meanH = 0
meanP = 0
meanR = 0
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

    aX, aY, aZ, h, p, r, sC, gC, aC, mC = [stringList[i] for i in range(0, 10)]

    # Here is where we're going to handle for the weight IDs. If more than 10 parameters are passed, we know that there
    # are IDs that need to be handled.
    if len(stringList) > 10:
        weightIDs.append([stringList[i] for i in range(11, len(stringList))])

    if not weightIDs:
        weight = calculateWeight(weightIDs)

    # TODO: we need to actually make the script handle for the IDs now that we have them collected. In order to do that

    dataset.loc[datetime.datetime.now()] = [float(aX) - meanAX, float(aY) - meanAY, float(aZ) - meanAZ, float(h) - meanH,
                                            float(p) - meanP,
                                            float(r) - meanR, int(sC), int(gC), int(aC), int(mC), float(weight)]
    return float(aX) - meanAX, float(aY) - meanAY, float(aZ) - meanAZ, float(h) - meanH, float(p) - meanP, float(r) - meanR, int(sC), int(gC), int(aC), int(mC), float(weight)


# TODO: finish all of the score calculations
def calculate_momentum(aX, aY, aZ, h, p, r, sC, gC, aC, mC, weight):
    return 'NA'


def calculate_effort(aX, aY, aZ, h, p, r, sC, gC, aC, mC, weight):
    return 'NA'


def calculate_stability(aX, aY, aZ, h, p, r, sC, gC, aC, mC, weight):
    return 'NA'


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
    meanH = dataset["heading"].mean()
    meanP = dataset["pitch"].mean()
    meanR = dataset["roll"].mean()
    print(meanAX, meanAY, meanAZ, meanH, meanP, meanR)


# Thread 1 is going to be used solely for listening in onto the MQTT channel and putting data into the queue.
# The first parameter is the queue that we want the data to flow into.
def thread_1_startMQTT(inputQueue):
    print("Thread 1 has begun")
    import mqtt
    mqtt.run(inputQueue)


# Thread 2 is going to be used for doing the initial processing of the data
# The first parameter is the queue that we want the data to flow out of, or in other words the data
# that we want to be processing.
def thread_2_processing(inputQueue, outboxQueue):
    global weight
    print("Thread 2 has begun")

    # First we declare all of the things that we're going to use frequently in the main processing loop
    movement_database = pd.DataFrame(columns=['aX', 'aY', 'aZ', 'heading', 'pitch', 'roll', 'systemStatus',
                                              'gyroStatus', 'accelStatus', 'magStatus', 'weight'])

    #findAverages(movement_database, inputQueue, 30)

    # This should empty the queue so that we can start fresh now that we have our averages
    while not inputQueue.empty():
        inputQueue.get()
        print(inputQueue.qsize())

    print("Main processing Loop has begun!")
    while True:
        # Todo: Once we have all the raw data, that stuff needs to be put into the queue to be sent to the server

        if not inputQueue.empty():
            aX, aY, aZ, h, p, r, sC, gC, aC, mC, weight = pull_from_queue(movement_database, inputQueue)
            momentum = calculate_momentum(aX, aY, aZ, h, p, r, sC, gC, aC, mC, weight)
            effort = calculate_effort(aX, aY, aZ, h, p, r, sC, gC, aC, mC, weight)
            stability = calculate_stability(aX, aY, aZ, h, p, r, sC, gC, aC, mC, weight)

            # Todo: we need to make it so that scores are only updated and put into the queue once a rep has been finished
        if keyboard.is_pressed('a'):
            print("A key has been pressed!")
            scores = [effort, momentum, stability, sC, gC, aC, mC]
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
# this is a change
