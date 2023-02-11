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


def adjust_for_spin(x, y, z, qw, qx, qy, qz):
    # First we need to initialize the rotational matrix
    rotation = Rotation.from_quat([float(qx), float(qy), float(qz), float(qw)])
    # Now we pull in the original XYZ data and apply the rotation
    adjustedXYZ = rotation.apply([float(x), float(y), float(z)])
    # now we just return it all and there we go.
    return adjustedXYZ
