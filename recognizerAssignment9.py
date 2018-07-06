#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

# the following sources were used to make the $1 recognizer
# source 1: http://depts.washington.edu/madlab/proj/dollar/dollar.js, last visited: 29.06.2018
# source 2: https://github.com/PetaPetaPeta/dollar-one-recognizer-python/blob/master/recognizer.py,
# last visited: 29.06.2018
# source 3: http://faculty.washington.edu/wobbrock/pubs/uist-07.01.pdf, last visited: 29.06.2018

# the code was written equally by Katharina Lichtner and Lucia Eckl

import wiimote
import sys
from PyQt5 import uic, QtWidgets, QtCore, QtGui, Qt
from transform import Transform
import math
from operator import itemgetter


class Window(QtWidgets.QWidget):

    # initialising all needed variables
    def __init__(self, app):
        super().__init__()
        self.start_pos = (0, 0)
        self.mouseMovePos = (0, 0)
        self.draw = False
        self.coordinates = []
        self.pointNumber = 64
        self.X = 0
        self.Y = 0
        self.resampledPoints = []
        self.square_size = 100
        self.drawNewPoints = False
        self.rotatedPoints = []
        self.scale = []
        self.origin = (100, 100)
        self.toOrigin = []
        self.addNewDefinedGetureButtonText = "Add gesture/symbol"
        self.addExistingGestureButtonText = "Add Symbol"
        self.resultButtonText = "Result"
        self.gestureInputText = ""
        self.dropdown = ""
        self.points = []
        self.transform = Transform()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.gestures = []
        self.gestureName = []
        self.gestureInput = ""
        self.resultOutputText = ""
        self.angle_range = 45
        self.angle_step = 2.0
        self.category = -1
        self.wm = 0
        self.checkDraw = False
        self.app = app
        self.resultButtonValues = []
        self.addSymbolButtonValues = []
        self.addGestureButtonValues = []
        self.dropdownValue = []
        self.initUI()

        # at every start of the programm it trys to connect with the wiimote
        try:
            self.connect_wiimote()
        except Exception:
            print("not connected To Wiimote")

# making Boxlayouts within a boxlayout
# https://stackoverflow.com/questions/49127653/align-every-widget-of-a-qhboxlayout-to-the-top-in-pyqt
# last accessed 25.06.2018
# line edit hint text:
# http://doc.qt.io/qt-5/qtwidgets-widgets-lineedits-example.html
# last access 25.06.2018

    # initialising everything for the user interface
    def initUI(self):

        self.layout = QtWidgets.QVBoxLayout(self)

        self.dropdown = QtWidgets.QComboBox(self)
        self.exampleText = QtWidgets.QLabel(self)
        self.pushButton = QtWidgets.QPushButton(self.addExistingGestureButtonText)
        self.addGestureButton = QtWidgets.QPushButton(self.addNewDefinedGetureButtonText)
        self.resultButton = QtWidgets.QPushButton(self.resultButtonText)
        self.exampleText.setText("Add example of type")
        self.addExamplelayout = QtWidgets.QHBoxLayout()
        self.addExamplelayout.addWidget(self.exampleText)
        self.dropdown.addItem("Snake")
        self.dropdown.addItem("Rectangle")
        self.dropdown.addItem("Circle")
        self.addExamplelayout.addWidget(self.dropdown)
        self.addExamplelayout.addWidget(self.pushButton)
        self.pushButton.clicked.connect(self.clickedButton)
        self.dropdown.activated.connect(self.getTextFromDropdown)
        self.addGestureText = QtWidgets.QLabel(self)
        self.addGestureText.setText("Add Gesture of type")
        self.addGestureLayout = QtWidgets.QHBoxLayout()
        self.addGestureLayout.addWidget(self.addGestureText)
        self.gestureInput = QtWidgets.QLineEdit("", self)
        self.gestureInput.setPlaceholderText("Add symbol/gesture of type")

        self.gestureInput.selectAll()
        self.gestureInput.setFocus()

        self.addGestureLayout.addWidget(self.gestureInput)

        self.addGestureLayout.addWidget(self.addGestureButton)
        self.addGestureButton.clicked.connect(self.addNewGesture)

        self.resultText = QtWidgets.QLabel(self)
        self.resultText.setText("Result: ")
        self.resultOutputText = QtWidgets.QLabel(self)
        self.resultLayout = QtWidgets.QHBoxLayout()

        self.resultLayout.addWidget(self.resultText)
        self.resultLayout.addWidget(self.resultOutputText)
        self.resultLayout.addWidget(self.resultButton)
        self.resultButton.clicked.connect(self.resultClicked)

        self.addExamplelayout.setAlignment(QtCore.Qt.AlignBottom)
        self.addGestureLayout.setAlignment(QtCore.Qt.AlignBottom)
        self.resultLayout.setAlignment(QtCore.Qt.AlignBottom)

        self.layout.addLayout(self.addExamplelayout)

        self.layout.addLayout(self.addGestureLayout)
        self.layout.addLayout(self.resultLayout)
        self.layout.setAlignment(QtCore.Qt.AlignBottom)

        self.setGeometry(0, 0, 1280, 720)
        self.setWindowTitle('$1 Recognizer')
        QtGui.QCursor.setPos(self.mapToGlobal(QtCore.QPoint(self.start_pos[0], self.start_pos[0])))

        self.show()

    # gets the selected item of the dropdown list
    def getTextFromDropdown(self):
        self.gestureInput.selectAll()
        self.gestureInput.setFocus()

    # connects with the given id of the wiimote and registers callbacks on it
    def connect_wiimote(self):
        self.wm = wiimote.connect("18:2A:7B:F3:F8:F5")

        if self.wm is not None:
            self.wm.ir.register_callback(self.process_wiimote_ir_data)
            self.wm.buttons.register_callback(self.getpressedButton)

    # if the 'B'-button on the wiimote is pressed, it draws and if the 'A'-Button is pressed on a bitton on the screen,
    # the button is clicked
    def getpressedButton(self, ev):
        x = self.cursor().pos().x()
        y = self.cursor().pos().y()
        self.values = True
        if self.wm.buttons["B"]:
            self.dropdown.hidePopup()
            if self.draw is False:
                self.coordinates = []
                self.update()
                self.gestureInput.selectAll()
                self.gestureInput.setFocus()
            self.draw = True
            if self.draw is True:

                self.mouseMovePos = x, y
                self.coordinates.append(self.mouseMovePos)
                self.update()
                self.checkDraw = True

        else:
            if len(self.coordinates) > 0 and self.checkDraw is True:
                self.draw = False
                self.points = self.resample(self.coordinates, self.pointNumber)
                angle = self.indicativeAngle(self.points)
                self.points = self.rotateBy(self.points, -angle)
                self.points = self.scaleToSquare(self.points)
                self.points = self.translateTo(self.points, self.origin)
                self.points = self.points
                self.update()
                self.checkDraw = False

        if self.wm.buttons["A"]:
            if self.values is True:
                self.addGestureButtonValues.append(self.addGestureButton.pos().x())
                self.addGestureButtonValues.append(self.addGestureButton.pos().y())
                self.addGestureButtonValues.append(self.addGestureButton.width())
                self.addGestureButtonValues.append(self.addGestureButton.height())
                self.addSymbolButtonValues.append(self.pushButton.pos().x())
                self.addSymbolButtonValues.append(self.pushButton.pos().y())
                self.addSymbolButtonValues.append(self.pushButton.width())
                self.addSymbolButtonValues.append(self.pushButton.height())
                self.resultButtonValues.append(self.resultButton.pos().x())
                self.resultButtonValues.append(self.resultButton.pos().y())
                self.resultButtonValues.append(self.resultButton.width())
                self.resultButtonValues.append(self.resultButton.height())

                self.values = False

            if x > self.resultButtonValues[0] and x < self.resultButtonValues[0] + self.resultButtonValues[2] \
                    and y > self.resultButtonValues[1] and y < self.resultButtonValues[1] + self.resultButtonValues[3]:
                self.resultClicked()
            elif x > self.addSymbolButtonValues[0] and x < self.addSymbolButtonValues[0] + \
                    self.addSymbolButtonValues[2] and y > self.addSymbolButtonValues[1] and \
                    y < self.addSymbolButtonValues[1] + self.addSymbolButtonValues[3]:
                self.clickedButton()
            elif x > self.addGestureButtonValues[0] and x < self.addGestureButtonValues[0] + \
                    self.addGestureButtonValues[2] and y > self.addGestureButtonValues[1] and \
                    y < self.addGestureButtonValues[1] + self.addGestureButtonValues[3]:
                self.addNewGesture()

    # gets the data from the wiimote and sets the cursor
    def process_wiimote_ir_data(self, event):
        if len(event) == 4:
            leds = []

            for led in event:
                leds.append((led["x"], led["y"]))
            P, DEST_W, DEST_H = (1024 / 2, 768 / 2), 1024, 768

            try:
                x, y = self.transform.transform(P, leds, DEST_W, DEST_H)
            except Exception as e:
                print(e)
                x = y = -1

            self.cursor().setPos(self.mapToGlobal(QtCore.QPoint(x, y)))

    # if the result button is clicked, it is prooved, wether the gesture was already trained and can be predicted and
    # if yes, if it is precisely enough made
    def resultClicked(self):
        if len(self.points) > 0 and len(self.gestures) > 0:
            self.category = self.recognize(self.points, self.gestures)
            if sorted(self.category, key=itemgetter(0))[0][0] <= 15:
                self.category = sorted(self.category, key=itemgetter(0))[0][1]
                self.prediction()
            else:
                self.resultOutputText.setText("no Gesture found")
        elif len(self.points) == 0:
            self.resultOutputText.setText("no Gesture found")
        elif len(self.gestures) == 0:
            self.resultOutputText.setText("no Gestures trained")

    # adds a new gesture of the input to the gesture list, if it is not yet trained and adds the associated points
    def addNewGesture(self):
        self.gestureInput.selectAll()
        self.gestureInput.setFocus()

        if self.gestureInput.text() not in self.gestureName:
            self.gestureName.append(self.gestureInput.text())
            self.gestures.append([self.points])
            self.dropdown.addItem(self.gestureInput.text())
        else:

            index = self.gestureName.index(self.gestureInput.text())

            self.gestures[index].append(self.points)

    # adds a new gesture of the droplist to the gesture list, if it is not trained yet and adds the associated points
    def clickedButton(self):
        self.gestureInput.selectAll()
        self.gestureInput.setFocus()

        if self.dropdown.currentText() not in self.gestureName:
            self.gestureName.append(self.dropdown.currentText())
            self.gestures.append([self.points])
        else:

            index = self.gestureName.index(self.dropdown.currentText())

            self.gestures[index].append(self.points)

    # sets the text of the predicted category to the label on the window
    def prediction(self):
        result = self.gestureName[self.category]
        self.resultOutputText.setText(result)

    # if the mouse is pressed, the window is emptied and a new drawing begins
    def mousePressEvent(self, ev):
        self.coordinates = []
        self.update()
        self.gestureInput.selectAll()
        self.gestureInput.setFocus()
        self.draw = True

    # if the mouse is released the drawed gesture makes the $1 recognition to unify the gestures
    # if only a point is drawn, an exception is thrown
    def mouseReleaseEvent(self, ev):
        self.draw = False
        try:
            self.points = self.resample(self.coordinates, self.pointNumber)
            angle = self.indicativeAngle(self.points)
            self.points = self.rotateBy(self.points, -angle)
            self.points = self.scaleToSquare(self.points)
            self.points = self.translateTo(self.points, self.origin)
            self.points = self.points
            self.update()
        except Exception:
            print("just one point, but no real gesture made")

    # if the mouse is moved, every single position is tracked
    def mouseMoveEvent(self, ev):
        if self.draw is True:
            self.mouseMovePos = ev.x(), ev.y()
            self.coordinates.append(self.mouseMovePos)
            self.update()

    # drawing the gesture that is actual made by the user (self.draw) or the little unified gesture (self.drawNewPoints)
    def paintEvent(self, event):
            qp = QtGui.QPainter()
            qp.begin(self)
            if self.draw is True:
                self.drawtarget(qp)
            elif self.drawNewPoints is True:
                self.drawNewTargetPoints(qp)
                self.drawNewPoints = False

            qp.end()

    # draws the unified gesture
    def drawNewTargetPoints(self, qp):
        qp.setBrush(QtGui.QColor(0, 200, 0))
        for i in range(len(self.points) - 1):
            qp.drawLine(self.points[i][0], self.points[i][1], self.points[i + 1][0], self.points[i + 1][1])

    # draws the actual gesture that is made by the user
    def drawtarget(self, qp):
        qp.setBrush(QtGui.QColor(0, 200, 0))
        for i in range(len(self.coordinates) - 1):
            qp.drawLine(self.coordinates[i][0], self.coordinates[i][1], self.coordinates[i + 1][0], self.coordinates[i + 1][1])

    # recognizes every distance for the points between the gesture that has to be predicted and every trained gesture
    # and returns all the distances and its indices for getting the categories later
    def recognize(self, points, templates):
        b = math.inf
        resultArray = []
        for i in range(len(templates)):
            for j in range(len(templates[i])):
                d = self.distanceAtBestAngle(points, templates[i][j], -self.angle_range, self.angle_range, self.angle_step)
                if(d < b):
                    b = d
                    resultArray.append([d, i])

        return resultArray

    # calculates the distances between the gesture that is made by the user and all the trained gestures
    def distanceAtBestAngle(self, points, T, a, b, threshold):
        phi = (-1 + 5**0.5)/2
        x1 = phi * a + (1.0 - phi) * b
        f1 = self.distanceAtAngle(points, T, x1)
        x2 = (1.0 - phi) * a + phi * b
        f2 = self.distanceAtAngle(points, T, x2)
        while (abs(b - a) > threshold):
            if f1 < f2:
                b = x2
                x2 = x1
                f2 = f1
                x1 = phi * a + (1.0 - phi) * b
                f1 = self.distanceAtAngle(points, T, x1)
            else:
                a = x1
                x1 = x2
                f1 = f2
                x2 = (1.0 - phi) * a + phi * b
                f2 = self.distanceAtAngle(points, T, x2)
        return min(f1, f2)

    # calculates the distance of the points of the gesture made by the user and the trained gestures at a certain angle
    def distanceAtAngle(self, points, T, radians):
        newpoints = self.rotateBy(points, radians)
        return self.pathDistance(newpoints, T)

    # calculates the distance of all points
    def pathDistance(self, pts1, pts2):
        d = 0.0
        for i in range(len(pts1)):
            d += self.distance(pts1[i], pts2[i])
        return d/len(pts1)

    # gets the points of the gesture made by the user and the number of points and calculates a new unified list of points
    def resample(self, points, numberOfPoints):
        intervalLength = self.pathLength(points) / float(numberOfPoints - 1)
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

        if len(newpoints) == numberOfPoints - 1:
            newpoints.append(points[-1])

        return newpoints

    # sets the x and y values of a point
    def point(self, x, y):
        self.X = x
        self.Y = y

    # returns the distance off all points of the gesture the user made
    def pathLength(self, points):
        d = 0.0
        for i in range(1, len(points)):
            d += self.distance(points[i - 1], points[i])
        return d

    # calculates the distance between two points
    def distance(self, p1, p2):
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        return float(math.sqrt(dx * dx + dy * dy))

    # returns the rotations angle for the gesture that is made by the user
    def indicativeAngle(self, points):
        centroid = self.centroid(points)
        rotation_angle = math.atan2(centroid[1] - points[0][1], centroid[0]-points[0][0])
        return rotation_angle

    # rotates the whole gesture that is made by the user and returns the new rotated points
    def rotateBy(self, points, radians):
        centroid = self.centroid(points)

        cos = math.cos(radians)
        sin = math.sin(radians)
        newPoints = []
        for i in range(len(points)):
            qx = (points[i][0] - centroid[0]) * cos - (points[i][1] - centroid[1]) * sin + centroid[0]
            qy = (points[i][0] - centroid[0]) * sin + (points[i][1] - centroid[1]) * cos + centroid[1]

            newPoints.append([qx, qy])

        return newPoints

    # scales the whole gesture that is made by the user and returns the new scaled points
    def scaleToSquare(self, points):
        b = self.boundingBox(points)
        newpoints = []
        for i in range(len(points)):
            qx = points[i][0] * (self.square_size / b[2])
            qy = points[i][1] * (self.square_size / b[3])
            newpoints.append([qx, qy])
        return newpoints

    # calculates the minimum and maximum values for every x and y of a point and returns them and the difference between minimum and maximum
    def boundingBox(self, points):
        minX = +math.inf
        maxX = -math.inf
        minY = +math.inf
        maxY = -math.inf
        for i in range(len(points)):
            minX = min(minX, points[i][0])
            minY = min(minY, points[i][1])
            maxX = max(maxX, points[i][0])
            maxY = max(maxY, points[i][1])

        return [minX, minY, maxX - minX, maxY - minY]

    # calculates the centroid of the drawn gesture made by the user
    def centroid(self, points):
        x = 0.0
        y = 0.0
        for i in range(len(points)):
            x += points[i][0]
            y += points[i][1]

        x = x / len(points)
        y = y / len(points)
        return [x, y]

    # translates the gesture to a unified place on the window and returns the new points
    def translateTo(self, points, origin):

        centroid = self.centroid(points)
        newpoints = []
        for i in range(len(points)):
            qx = points[i][0] + origin[0] - centroid[0]
            qy = points[i][1] + origin[1] - centroid[1]
            newpoints.append([qx, qy])
        self.drawNewPoints = True
        return newpoints


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = Window(app)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
