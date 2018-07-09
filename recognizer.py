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
from operator import itemgetter


class Recognizer:

    def __init__(self):
        """init recognizer"""
        self.gestures = []
        self.gestureName = ["Circle", "Circle", "Check"]
        self.N = 64
        self.category = -1
        self.size = 100
        self.origin = 100, 100
        self.ratio = 1/2 * (-1 + np.sqrt(5))
        self.recognizedName = "gesture not found"
        self.angle_range = 45
        self.angle_step = 2
        self.template = [[[46.241379099071196, 99.99999999999983], [49.66373813278733, 103.33565207034556], [50.74521909640532, 108.02229853907087], [51.118141167990984, 113.11787664173542], [53.34329493772907, 117.14447354428117], [54.409414960262666, 122.05706104272755], [56.37261000595777, 126.60389068628095], [59.794969039674015, 129.9395427566267], [62.38917823124132, 133.75314616158218], [63.94452959099192, 138.1663071126674], [67.36688862470828, 141.50195918301316], [70.78924765842453, 144.83761125335892], [74.21160669214066, 148.17326332370462], [77.63396572585702, 151.50891539405032], [80.84242876443534, 151.68637164277587], [84.07852743590854, 152.27187078299986], [87.29448697673274, 152.5600136392724], [91.74420003387547, 152.31973428533158], [95.91549651090736, 151.2032004682534], [98.84831725724393, 147.31077062556975], [103.1487524590068, 146.48368589808453], [106.08157320534349, 142.59125605540092], [109.01439395168006, 138.6988262127173], [111.94721469801664, 134.8063963700337], [114.88003544435333, 130.91396652735003], [118.99108067962993, 129.66238671915508], [122.11329139245277, 126.1944519571812], [125.04611213878945, 122.30202211449759], [127.97893288512603, 118.40959227181398], [130.9117536314626, 114.51716242913037], [133.8445743777993, 110.62473258644675], [136.77739512413586, 106.73230274376314], [139.71021587047244, 102.83987290107953], [142.64303661680924, 98.94744305839589], [144.90230479861407, 94.80469475000348], [145.6358644979913, 90.09493352153422], [146.2413790990712, 85.33758572857832], [145.89522325641462, 80.22655999290353], [144.75154937223795, 76.62727830670931], [143.42276924485088, 72.95920390375696], [142.39118117557496, 68.24376267564793], [138.96882214185882, 64.9081106053022], [135.54646310814246, 61.57245853495647], [132.1241040744262, 58.23680646461074], [128.70174504070985, 54.901154394265006], [124.99366598612528, 52.5600136392724], [120.49987526799032, 52.953714977706426], [116.00608454985525, 53.347416316140425], [111.51229383172029, 53.74111765457445], [108.13836899514592, 55.770434160536496], [104.97209231288093, 56.21586369399813], [101.90020677798657, 58.05498798566023], [98.78112566940672, 59.19726489822207], [95.5670742235983, 58.93729525623368], [92.33097555212498, 58.351796116009695], [88.51314165903568, 60.26057426832048], [85.06280860942161, 62.55584634933501], [81.86162093255246, 62.48581154595456], [77.6296399459361, 63.46632825361641], [74.6283649844529, 67.20532611612342], [71.69554423811633, 71.09775595880703], [68.76272349177975, 74.99018580149064], [65.82990274544306, 78.88261564417425], [62.89708199910717, 82.7750454868569]], [[51.351515402270934, 100.00000000000004], [55.30661825123798, 96.9123931171214], [57.295617376002156, 93.45283018767019], [58.107034046930835, 89.13052898531238], [59.57577721045095, 85.28727940298283], [60.90744984262369, 81.34866485350337], [62.93933815449492, 77.89721588685116], [65.63108017541231, 73.93064280546803], [68.3228221963297, 69.9640697240849], [72.27792504529674, 66.87646284120626], [76.23302789426378, 63.788855958327616], [80.18813074323094, 60.701249075448985], [84.14323359219799, 57.61364219257034], [88.57032462171986, 55.81595477172846], [92.88418448777969, 53.708812395283246], [97.42452887343887, 52.91426195574607], [101.8136161135962, 52.16202724329433], [105.92514646300418, 51.80064436279467], [110.65908352662547, 51.29277277835773], [114.88319288774795, 52.74579376555657], [119.10146239873342, 53.823480896239374], [123.87633915925431, 54.72681283180884], [128.10280800101208, 57.05540070198012], [131.9961600803527, 59.70162027946914], [136.1124128188332, 62.01963070104556], [139.61871205920016, 65.35236111598236], [143.71650460325412, 67.4411150297393], [146.51409722767602, 71.80622618722502], [149.3116898520978, 76.17133734471075], [151.35151540227088, 80.72604477964695], [150.52920049298103, 85.99324647417548], [148.0321376365145, 89.99664980589982], [146.98330118674488, 93.63407679583834], [143.88403208279323, 96.93949217107935], [142.17221774512512, 101.58783667629599], [139.65355863453618, 105.67482985013386], [137.43712495408926, 110.10460461179584], [135.20858524524982, 114.55720206026446], [132.5619124293101, 118.85140139319584], [129.95676708304262, 122.87822293901623], [127.68892596658219, 127.31593214065761], [125.42781683107722, 131.70216938343316], [121.806323883831, 135.11488873305666], [118.58030151650809, 138.91300556369208], [114.62519866754104, 142.0006124465707], [110.67009581857377, 145.08821932944937], [106.71499296960673, 148.175826212328], [102.27993672809765, 149.95174511780266], [97.94374329991905, 151.2927727783577], [93.98134843118618, 150.69393546924988], [90.03249796593906, 150.00789148320376], [86.40706206248359, 150.97291254348914], [82.0493651105441, 149.50662556972162], [77.34833727287315, 148.4740008016169], [73.8593773791851, 146.86473127577779], [69.83067262063139, 144.65502020873845], [66.23667376726632, 141.6842370010026], [63.439081142844486, 137.31912584351687], [60.64148851842259, 132.95401468603114], [57.843895894000696, 128.58890352854547], [55.0463032695788, 124.22379237105973], [52.248710645156905, 119.85868121357403], [52.314495232825266, 116.0352762003492], [52.42316900760068, 112.21998514992335]]
                         , [[32.85397408659128, 100.0], [35.82976950776629, 101.92647744088501], [40.36602210607771, 103.00960416636298], [44.419036373067684, 104.55205743863323], [48.34668634145305, 106.21367168518233], [52.27433630983819, 107.87528593173144], [55.29048508362803, 109.9211731298424], [57.88154704533599, 112.05558017176784], [62.41779964364753, 113.13870689724578], [66.40008490686591, 114.70482081302364], [69.9042735480873, 116.6273379690351], [73.08915457815658, 118.72242525785501], [77.03313438205214, 119.1338760003998], [80.75106744834227, 120.858878139897], [84.43760744722852, 122.68284331371038], [88.45404039235041, 124.21918490918515], [91.4375786985795, 126.14147769973479], [94.40563123470042, 128.07213979095522], [98.94188383301196, 129.15526651643316], [101.91767925418696, 131.08174395731822], [106.1140009179594, 132.46124607637674], [109.59313434887144, 134.36587551396948], [112.87116762599874, 136.12900818911857], [115.85430075641989, 137.7527481260548], [118.87408578248574, 138.76111312325352], [120.77223265460805, 137.1384267073214], [119.93885936916706, 134.5991209881105], [120.19545914813716, 132.06795857798474], [118.36733505573761, 129.52122096568556], [116.86126904438493, 126.94793141124387], [117.2775612497428, 124.21615384749208], [115.77478108220748, 121.64259339304797], [113.94665698980793, 119.09585578074879], [112.54712761920177, 116.47637812266478], [111.49799267958736, 113.79743238049795], [110.4488577399726, 111.11848663833109], [109.36448884564868, 108.4455207166063], [107.53636475324913, 105.89878310430711], [108.7877153391778, 103.37505258726961], [106.95959124677825, 100.82831497497045], [105.13146715437881, 98.2815773626713], [105.24893255970926, 95.60495372259919], [105.93751818230419, 92.89020254509549], [106.62610380489923, 90.17545136759176], [107.31468942749427, 87.46070019008803], [108.04595963823749, 84.75012272696134], [109.06933696665772, 82.0681076028325], [110.02744641453614, 79.38334655849232], [109.7437058581587, 76.64633897270173], [109.89927195777977, 73.94396285316407], [111.54409871276516, 71.3589882785923], [113.18892546775055, 68.77401370402055], [114.83375222273582, 66.18903912944882], [116.47857897772133, 63.604064554877034], [118.12340573270671, 61.01908998030529], [119.57042419268578, 58.41852176243331], [119.28668363630834, 55.6815141766427], [119.62958830656578, 53.005780186432], [121.58048301970473, 50.48727604079081], [123.53137773284368, 47.968771895149594], [125.48227244598263, 45.450267749508406], [127.43316715912158, 42.9317636038672], [129.38406187226053, 40.41325945822599], [132.85397408659117, 38.761113123253516]]]


    def recognizeGesture(self, gest):
        """when the mode is "recognize" the input gesture are resampled, rotated, scaled and translated and at least
        the recognition is started. If the result of recognition is -1 no agreement is found otherwise the name of the
        gesture is defined by the value which is returned after recognition"""
        gesture = []
        result = "gesture not found"
        gesture = gest
        gesture = self.resample(gesture)
        gesture = self.rotate(gesture)
        gesture = self.scale(gesture)
        gesture = self.translate(gesture)
        self.category = self.recognize(gesture, self.template)
        if sorted(self.category, key=itemgetter(0))[0][0] <= 15:
            self.category = sorted(self.category, key=itemgetter(0))[0][1]
            result = self.gestureName[self.category]

        return result

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

    def resample(self, points):
        """the input gestures are sampled to the length n and the list newPoints is returned"""
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
            d = self.distance(gesture[i - 1], gesture[i])
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

    def recognize(self, points, templates):
        b = math.inf
        resultArray = []
        for i in range(len(templates)):
            for j in range(len(templates[i])):
                d = self.distanceAtBestAngle(points, templates[i], -self.angle_range, self.angle_range, self.angle_step)
                if(d < b):
                    b = d
                    resultArray.append([d, i])

        return resultArray

    def recognized(self, points):
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