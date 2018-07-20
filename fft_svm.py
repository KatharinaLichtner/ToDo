#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

import numpy as np

# Katharina Lichtner
# oriented at jupyter notebooks "dft_tour" and "machine_learning_tour"
# from the course Interaktionstechniken und -technologien


class ActivityRecognzer():
    def __init__(self):
        self._bufferX = np.array([])
        self._bufferY = np.array([])
        self._bufferZ = np.array([])

    # fft reads in the accelerometer data of x-,y- and z-axis.
    # calculate frequency components of the raw data from every movement with the furier transformations
    def fft(self, x, y, z):
        size = 32
        self._bufferX = np.append(self._bufferX, x)
        self._bufferX = self._bufferX[-size:]
        self._bufferY = np.append(self._bufferY, y)
        self._bufferY = self._bufferY[-size:]
        self._bufferZ = np.append(self._bufferZ, z)
        self._bufferZ = self._bufferZ[-size:]

        for i in range(len(self._bufferX)):
            xValue = self._bufferX[i]
            yValue = self._bufferY[i]
            zValue = self._bufferZ[i]
            avgValue = ((xValue + yValue + zValue) / 3)
            self._avg = np.append(self._avg, avgValue)
            self._avg = self._avg[-size:]

        avg = np.fft.fft(self._avg / len(self._avg))
        avgfft = abs(avg)
        return avgfft

    # with the trained data it is possible to predict the current input movement of the wiimote
    def svm(self, data):
        self.c.fit(self.trainingDataTest, self.featureVector)
        predicted = self.c.predict([data[1:]])
        self.predicted = predicted[0]
        return self.predicted


def main():
    app = ActivityRecognzer()


if __name__ == '__main__':
    main()
