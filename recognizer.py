#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

"""The implementation of the $1 Recognizer is written after the paper "Gestures without Libraries, Toolkits or Training:
A $1 Recognizer for User Interface Prototypes" from Jacob O. Wobbrock, Andrew D. Wilson and Yang Li (2007).
Other used sources are:
'http://depts.washington.edu/madlab/proj/dollar/dollar.js' and
'https://github.com/PetaPetaPeta/dollar-one-recognizer-python/blob/master/recognizer.py'.
The $1 Recognizer gets a list of points which describes a gesture which is drawn on the screen. These points are
resampled, rotated, scaled and translated. The given input gesture is compared with the templates. If the distance
between input and template is under 15 the gesture is recognized and the category of the gestures is returned."""

import numpy as np
import math
from template_recognizer import Template
from operator import itemgetter


class Recognizer:

    # init recognizer
    def __init__(self):
        self.gestures = []
        self.gestureName = ["Circle", "Circle", "Check", "Uncheck", "Uncheck", "Edit", "Edit"]
        self.N = 64
        self.category = -1
        self.size = 100
        self.origin = 100, 100
        self.ratio = 1/2 * (-1 + np.sqrt(5))
        self.recognizedName = "gesture not found"
        self.angle_range = 45
        self.angle_step = 2
        self.template = Template.template

    # the input gesture are resampled, rotated, scaled and translated and at least the recognition is started.
    # the category of the result is returned otherwise "no valid gesture" is returned
    def recognizeGesture(self, gest):
        gesture = []
        result = "gesture not found"
        gesture = gest
        try:
            if len(gesture) > 1:
                gesture = self.resample(gesture)
                gesture = self.rotate(gesture)
                gesture = self.scale(gesture)
                gesture = self.translate(gesture)
                self.category = self.recognize(gesture, self.template)
                if sorted(self.category, key=itemgetter(0))[0][0] <= 15:
                    self.category = sorted(self.category, key=itemgetter(0))[0][1]
                    result = self.gestureName[self.category]
                return result
            else:
                return "no valid gesture"
        except Exception as e:
            print(e)

    # returns the name of the recognized gesture
    def getGestureName(self):
        return self.recognizedName

    # the input gestures are sampled to the length n and the list newPoints is returned
    def resample(self, points):
        intervalLength = self.pathLength(points) / float(self.N - 1)
        D = 0.0
        newpoints = [points[0]]
        i = 1
        while i < len(points):
            point = points[i - 1]
            next_point = points[i]
            d = self.distance(point, next_point)
            if d + D >= intervalLength:
                delta_distance = float((intervalLength - D) / d)
                self.q = [0.0, 0.0]
                self.q[0] = points[i-1][0] + delta_distance * (points[i][0] - points[i-1][0])
                self.q[1] = points[i-1][1] + delta_distance * (points[i][1] - points[i-1][1])
                newpoints.append(self.q)
                points.insert(i, self.q)
                D = 0.0

            else:
                D += d
            i += 1

        if len(newpoints) == self.N - 1:
            newpoints.append(points[-1])
        return newpoints

    # the centroid of the gesture is calculated and returned
    def centroid(self, gesture):
        x = y = 0
        for i in range(len(gesture)):
            x = x + gesture[i][0]
            y = y + gesture[i][1]

        x = x/len(gesture)
        y = y/len(gesture)
        return x, y

    # the length of the gesture including all points is calculated and returned
    def pathLength(self, gesture):
        distance = 0.0
        for i in range(1, len(gesture)):
            d = self.distance(gesture[i - 1], gesture[i])
            distance += d

        return distance

    # the gesture is rotated and returned
    def rotate(self, gesture):
        centroid = self.centroid(gesture)
        radians = np.arctan2(centroid[1]-gesture[0][1], centroid[0]-gesture[0][0])
        newPoints = self.rotateBy(gesture, radians)
        return newPoints

    # the gesture is rotated depending on the given angle
    def rotateBy(self, gesture, radians):
        centroid = self.centroid(gesture)
        cos = np.cos(-radians)
        sin = np.sin(-radians)
        newPoints = []
        for i in range(len(gesture)):
            x = (gesture[i][0] - centroid[0]) * cos - (gesture[i][1] - centroid[1]) * sin + centroid[0]
            y = (gesture[i][0] - centroid[0]) * sin + (gesture[i][1] - centroid[1]) * cos + centroid[1]
            newPoints.append([float(x), float(y)])
        return newPoints

    # the gesture is scaled to a defined size and the calculated newPoints are returned
    def scale(self, gesture):
        self.boundingBox = self.getBoundingBox(gesture)
        newPoints = []
        for i in range(len(gesture)):

            x = gesture[i][0] * (self.size / (self.boundingBox[1][0] - self.boundingBox[0][0]))
            y = gesture[i][1] * (self.size / (self.boundingBox[1][1] - self.boundingBox[0][1]))

            newPoints.append([float(x), float(y)])

        return newPoints

    # defines the minimum and maximum points of the gesture and returns these
    def getBoundingBox(self, gesture):
        minX, minY = np.min(gesture, 0)
        maxX, maxY = np.max(gesture, 0)

        return (minX, minY), (maxX, maxY)

    # the gesture is translated depending on the given origin point, the calculated new points are returned
    def translate(self, gesture):
        newPoints = []
        c = np.mean(gesture, 0)
        for i in range(len(gesture)):
            x = gesture[i][0] + self.origin[0] - c[0]
            y = gesture[i][1] + self.origin[1] - c[1]
            newPoints.append([float(x), float(y)])

        return newPoints

    # calculates the distance between points and templates and
    # returns a result array
    def recognize(self, points, templates):
        b = math.inf
        resultArray = []
        for i in range(len(templates)):
            for j in range(len(templates[i])):
                d = self.distanceAtBestAngle(points, templates[i], -self.angle_range, self.angle_range, self.angle_step)
                if d < b:
                    b = d
                    resultArray.append([d, i])

        return resultArray

    """def recognized(self, points):
        numGesture = -1
        b = np.inf
        angle = 45
        a = 2
        for i in range(len(self.template)):
            template = self.template[i]
            d = self.distanceAtBestAngle(points, template, - angle, angle, a)
            if d < b:
                b = d
                numGesture = i
        if b < 15:
            return numGesture
        else:
            return -1"""

    # the minimum distance in dependence on the angle is calculated
    def distanceAtBestAngle(self, points, T, minAngle, angle, a):
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

    # the distance between points and template is calculated
    def distanceAtAngle(self, points, T, x1):
        newPoints = self.rotateBy(points, x1)
        d = self.pathDistance(newPoints, T)
        return d

    # calculates the distance of all points
    def pathDistance(self, pts1, pts2):
        d = 0.0
        for i in range(len(pts1)):
            d += self.distance(pts1[i], pts2[i])
        return d/len(pts1)

    # calculates the distance between two points
    def distance(self, p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return float(math.sqrt(dx * dx + dy * dy))
