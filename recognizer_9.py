#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

"""The implementation of the $1 Recognizer is written after the paper "Gestures without Libraries, Toolkits or Training:
A $1 Recognizer for User Interface Prototypes" from Jacob O. Wobbrock, Andrew D. Wilson and Yang Li (2007).
Other used sources are:
'http://depts.washington.edu/madlab/proj/dollar/dollar.js' and
'https://github.com/PetaPetaPeta/dollar-one-recognizer-python/blob/master/recognizer.py'.
The $1 Recognizer gets a list of points which describes a gesture which is drawn on the screen. These points are
resampled, rotated, scaled and translated. When the mode is "recognize" the input gesture is compared with the templates
of the created gestures. If the distance between input and template is under 15 the gesture is recognized and the name
of the gestures is returned.
by Miriam Schlindwein"""

import numpy as np
import math


class Recognizer:

    def __init__(self):
        """init recognizer"""
        self.gestures = []
        self.names = []
        self.N = 64
        self.size = 100
        self.origin = 100, 100
        self.ratio = 1/2 * (-1 + np.sqrt(5))
        self.recognizedName = "gesture not found"

    def recognizeGesture(self, gest):
        """when the mode is "recognize" the input gesture are resampled, rotated, scaled and translated and at least
        the recognition is started. If the result of recognition is -1 no agreement is found otherwise the name of the
        gesture is defined by the value which is returned after recognition"""
        gesture = []
        gesture = gest
        gesture = self.resample(gesture)
        gesture = self.rotate(gesture)
        gesture = self.scale(gesture)
        gesture = self.translate(gesture)
        numGesture = self.recognize(gesture)
        if numGesture == -1:
            self.recognizedName = "gesture not found"
        else:
            self.recognizedName = self.names[numGesture]

    def getGestureName(self):
        """returns the name of the recognized gesture"""
        return self.recognizedName

    def addTitleGesture(self, title):
        """when a new gesture is created the given name is added"""
        self.names.append(title)

    def addGesture(self, gest):
        """when the mode is adding new gesture the input gestures are resampled, rotated, scaled and translated,
        after that the processed gesture is added to the gesture list"""
        gesture = []
        gesture = gest
        gesture = self.resample(gesture)
        gesture = self.rotate(gesture)
        gesture = self.scale(gesture)
        gesture = self.translate(gesture)
        self.gestures.append(gesture)

    def resample(self, gesture):
        """the input gestures are sampled to the length n and the list newPoints is returned"""
        newPoints = [gesture[0]]
        distance = 0.0
        path = self.pathLength(gesture)
        pathLen = path / (self.N - 1)
        i = 1
        while i < len(gesture):
            d = self.Distance(gesture[i-1], gesture[i])
            if distance + d >= pathLen:
                x = gesture[i-1][0] + ((pathLen - distance)/d) * (gesture[i][0] - gesture[i-1][0])
                y = gesture[i-1][1] + ((pathLen - distance)/d) * (gesture[i][1] - gesture[i-1][1])
                q = (x, y)
                newPoints.append(q)
                gesture.insert(i, q)
                distance = 0.0
            else:
                distance += d
            i += 1
        if len(newPoints) == self.N - 1:
            newPoints.append(gesture[len(gesture)-1])
        return newPoints

    def Distance(self, p1, p2):
        """the distance between two points is calculated and returned"""
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return math.sqrt(dx*dx + dy*dy)

    def centroid(self, gesture):
        """the centroid of the gesture is calculated and returned"""
        x = y = 0
        for i in range(len(gesture)):
            x = x + gesture[i][0]
            y = y + gesture[i][1]

        x = x/len(gesture)
        y = y/len(gesture)
        return x, y

    def pathLength(self, gesture):
        """the length of the gesture including all points is calculated and returned"""
        distance = 0.0
        for i in range(1, len(gesture)):
            d = self.Distance(gesture[i - 1], gesture[i])
            distance += d

        return distance

    def rotate(self, gesture):
        """the gesture is rotated and returned"""
        centroid = self.centroid(gesture)
        radians = np.arctan2(centroid[1]-gesture[0][1], centroid[0]-gesture[0][0])
        newPoints = self.rotateBy(gesture, radians)
        return newPoints

    def rotateBy(self, gesture, radians):
        """the gesture is rotated depending on the given angle"""
        centroid = self.centroid(gesture)
        cos = np.cos(-radians)
        sin = np.sin(-radians)
        newPoints = []
        for i in range(len(gesture)):
            x = (gesture[i][0] - centroid[0]) * cos - (gesture[i][1] - centroid[1]) * sin + centroid[0]
            y = (gesture[i][0] - centroid[0]) * sin + (gesture[i][1] - centroid[1]) * cos + centroid[1]
            newPoints.append([float(x), float(y)])
        return newPoints

    def scale(self, gesture):
        """the gesture is scaled to a defined size and the calculated newPoints are returned"""
        self.boundingBox = self.getBoundingBox(gesture)
        newPoints = []
        for i in range(len(gesture)):

            x = gesture[i][0] * (self.size / (self.boundingBox[1][0] - self.boundingBox[0][0]))
            y = gesture[i][1] * (self.size / (self.boundingBox[1][1] - self.boundingBox[0][1]))

            newPoints.append([float(x), float(y)])

        return newPoints

    def getBoundingBox(self, gesture):
        """defines the minimum and maximum points of the gesture and returns these"""
        minX, minY = np.min(gesture, 0)
        maxX, maxY = np.max(gesture, 0)

        return (minX, minY), (maxX, maxY)

    def translate(self, gesture):
        """the gesture is translated depending on the given origin point, the calculated new points are returned"""
        newPoints = []
        c = np.mean(gesture, 0)
        for i in range(len(gesture)):
            x = gesture[i][0] + self.origin[0] - c[0]
            y = gesture[i][1] + self.origin[1] - c[1]
            newPoints.append([float(x), float(y)])

        return newPoints

    def recognize(self, points):
        """calculates the distance between points and templates and returns the number of template
        if there is no recognition -1 is returned"""
        numGesture = -1
        b = np.inf
        angle = 45
        a = 2
        for i in range(len(self.gestures)):
            template = self.gestures[i]
            d = self.distanceAtBestAngle(points, template, - angle, angle, a)
            if d < b:
                b = d
                numGesture = i
        if b < 15:
            return numGesture
        else:
            return -1

    def distanceAtBestAngle(self, points, T, minAngle, angle, a):
        """the minimum distance in dependence on the angle is calculated"""
        x1 = self.ratio * minAngle + (1-self.ratio) * angle
        f1 = self.distanceAtAngle(points, T, x1)
        x2 = (1-self.ratio) * minAngle + self.ratio * angle
        f2 = self.distanceAtAngle(points, T, x2)

        while np.abs(angle - minAngle) > a:
            if f1 < f2:
                angle = x2
                x2 = x1
                f2 = f1
                x1 = self.ratio*minAngle + (1 - self.ratio) * angle
                f1 = self.distanceAtAngle(points, T, x1)
            else:
                minAngle = x1
                x1 = x2
                f1 = f2
                x2 = (1-self.ratio)*minAngle + self.ratio*angle
                f2 = self.distanceAtAngle(points, T, x2)

        return min(f1, f2)

    def distanceAtAngle(self, points, T, x1):
        """the distance between points and template is calculated"""
        newPoints = self.rotateBy(points, x1)
        d = self.pathDistance(newPoints, T)
        return d

    def pathDistance(self, A, B):
        """the path Distance between gesture A and a gesture from the """
        d = 0
        for i in range(len(A)):
            d += self.Distance(A[i], B[i])
        return d/len(A)
