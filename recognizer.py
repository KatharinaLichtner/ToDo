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
        #self.names = []
        self.N = 64
        self.size = 100
        self.origin = 100, 100
        self.ratio = 1/2 * (-1 + np.sqrt(5))
        self.recognizedName = "gesture not found"
        self.template = [[[46.241379099071196, 99.99999999999983], [49.66373813278733, 103.33565207034556], [50.74521909640532, 108.02229853907087], [51.118141167990984, 113.11787664173542], [53.34329493772907, 117.14447354428117], [54.409414960262666, 122.05706104272755], [56.37261000595777, 126.60389068628095], [59.794969039674015, 129.9395427566267], [62.38917823124132, 133.75314616158218], [63.94452959099192, 138.1663071126674], [67.36688862470828, 141.50195918301316], [70.78924765842453, 144.83761125335892], [74.21160669214066, 148.17326332370462], [77.63396572585702, 151.50891539405032], [80.84242876443534, 151.68637164277587], [84.07852743590854, 152.27187078299986], [87.29448697673274, 152.5600136392724], [91.74420003387547, 152.31973428533158], [95.91549651090736, 151.2032004682534], [98.84831725724393, 147.31077062556975], [103.1487524590068, 146.48368589808453], [106.08157320534349, 142.59125605540092], [109.01439395168006, 138.6988262127173], [111.94721469801664, 134.8063963700337], [114.88003544435333, 130.91396652735003], [118.99108067962993, 129.66238671915508], [122.11329139245277, 126.1944519571812], [125.04611213878945, 122.30202211449759], [127.97893288512603, 118.40959227181398], [130.9117536314626, 114.51716242913037], [133.8445743777993, 110.62473258644675], [136.77739512413586, 106.73230274376314], [139.71021587047244, 102.83987290107953], [142.64303661680924, 98.94744305839589], [144.90230479861407, 94.80469475000348], [145.6358644979913, 90.09493352153422], [146.2413790990712, 85.33758572857832], [145.89522325641462, 80.22655999290353], [144.75154937223795, 76.62727830670931], [143.42276924485088, 72.95920390375696], [142.39118117557496, 68.24376267564793], [138.96882214185882, 64.9081106053022], [135.54646310814246, 61.57245853495647], [132.1241040744262, 58.23680646461074], [128.70174504070985, 54.901154394265006], [124.99366598612528, 52.5600136392724], [120.49987526799032, 52.953714977706426], [116.00608454985525, 53.347416316140425], [111.51229383172029, 53.74111765457445], [108.13836899514592, 55.770434160536496], [104.97209231288093, 56.21586369399813], [101.90020677798657, 58.05498798566023], [98.78112566940672, 59.19726489822207], [95.5670742235983, 58.93729525623368], [92.33097555212498, 58.351796116009695], [88.51314165903568, 60.26057426832048], [85.06280860942161, 62.55584634933501], [81.86162093255246, 62.48581154595456], [77.6296399459361, 63.46632825361641], [74.6283649844529, 67.20532611612342], [71.69554423811633, 71.09775595880703], [68.76272349177975, 74.99018580149064], [65.82990274544306, 78.88261564417425], [62.89708199910717, 82.7750454868569]], [[32.85397408659128, 100.0], [35.82976950776629, 101.92647744088501], [40.36602210607771, 103.00960416636298], [44.419036373067684, 104.55205743863323], [48.34668634145305, 106.21367168518233], [52.27433630983819, 107.87528593173144], [55.29048508362803, 109.9211731298424], [57.88154704533599, 112.05558017176784], [62.41779964364753, 113.13870689724578], [66.40008490686591, 114.70482081302364], [69.9042735480873, 116.6273379690351], [73.08915457815658, 118.72242525785501], [77.03313438205214, 119.1338760003998], [80.75106744834227, 120.858878139897], [84.43760744722852, 122.68284331371038], [88.45404039235041, 124.21918490918515], [91.4375786985795, 126.14147769973479], [94.40563123470042, 128.07213979095522], [98.94188383301196, 129.15526651643316], [101.91767925418696, 131.08174395731822], [106.1140009179594, 132.46124607637674], [109.59313434887144, 134.36587551396948], [112.87116762599874, 136.12900818911857], [115.85430075641989, 137.7527481260548], [118.87408578248574, 138.76111312325352], [120.77223265460805, 137.1384267073214], [119.93885936916706, 134.5991209881105], [120.19545914813716, 132.06795857798474], [118.36733505573761, 129.52122096568556], [116.86126904438493, 126.94793141124387], [117.2775612497428, 124.21615384749208], [115.77478108220748, 121.64259339304797], [113.94665698980793, 119.09585578074879], [112.54712761920177, 116.47637812266478], [111.49799267958736, 113.79743238049795], [110.4488577399726, 111.11848663833109], [109.36448884564868, 108.4455207166063], [107.53636475324913, 105.89878310430711], [108.7877153391778, 103.37505258726961], [106.95959124677825, 100.82831497497045], [105.13146715437881, 98.2815773626713], [105.24893255970926, 95.60495372259919], [105.93751818230419, 92.89020254509549], [106.62610380489923, 90.17545136759176], [107.31468942749427, 87.46070019008803], [108.04595963823749, 84.75012272696134], [109.06933696665772, 82.0681076028325], [110.02744641453614, 79.38334655849232], [109.7437058581587, 76.64633897270173], [109.89927195777977, 73.94396285316407], [111.54409871276516, 71.3589882785923], [113.18892546775055, 68.77401370402055], [114.83375222273582, 66.18903912944882], [116.47857897772133, 63.604064554877034], [118.12340573270671, 61.01908998030529], [119.57042419268578, 58.41852176243331], [119.28668363630834, 55.6815141766427], [119.62958830656578, 53.005780186432], [121.58048301970473, 50.48727604079081], [123.53137773284368, 47.968771895149594], [125.48227244598263, 45.450267749508406], [127.43316715912158, 42.9317636038672], [129.38406187226053, 40.41325945822599], [132.85397408659117, 38.761113123253516]]]


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
        return numGesture

    def getGestureName(self):
        """returns the name of the recognized gesture"""
        return self.recognizedName


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
        print(gesture)

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
        for i in range(len(self.template)):
            template = self.template[i]
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
