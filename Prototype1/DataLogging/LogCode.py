#setup matplotlib

import serial
import numpy
import matplotlib.pyplot as plt
from drawnow import *
from mpl_toolkits.mplot3d import Axes3D

#setup data
eulerX = []
eulerY = []
eulerZ = []
arduinoData = serial.Serial('com3', 115200)
plt.ion()
cnt=0

#setup for plotting 3D data
def makeFig()
    fig = plt.figure()
    ax = fig.add_subplot(111,projection='3d')
    #ax=Axes3D(fig)
    ax.plot_wireframe(eulerX, eulerY, eulerZ, rstride=5, cstride=5)
    plt.title('Prototype1 Euler Angle Data')
    plt.xlabel('EulerX (deg)')
    plt.ylabel('EulerY (deg)')
    plt.zlabel('EulerZ (deg)')
    #plt.plot(eulerX, 'r--', label='X', eulerY, 'bs', label='Y',eulerZ, 'g^', label='Z')
    #plt.plot(eulerX, 'r--', label='X')
    plt.legend(loc='upper left')

while True:
    while (arduinoData.inWaiting()==0):
        pass
    arduinoString = arduinoData.readline()
    dataArray = arduinoString.split(',')
    euX = float(dataArray[0])
    euY = float(dataArray[1])
    euZ = float(dataArray[2])
    eulerX.append(euX)
    eulerY.append(euY)
    eulerZ.append(euZ)
    drawnow(makeFig)
    plt.pause(.000001)
    cnt=cnt+1
    if(cnt>50):
        eulerX.pop(0)
        eulerY.pop(0)
        eulerZ.pop(0)
