#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

"""The class Window handles all click and move events of mouse or of wiimote.
by Miriam Schlindwein"""

import wiimote
import sys
from transform import Transform
from recognizer import Recognizer
from PyQt5 import QtWidgets, QtCore, QtGui


class Window(QtWidgets.QWidget):

    """init class Window and starts initUI()"""
    def __init__(self):
        super().__init__()
        self.wm = None
        self.setGeometry(0, 0, 1280, 720)
        self.draw = False
        self.qp = QtGui.QPainter()
        self.transformer = Transform()
        self.recognizer = Recognizer()
        self.pos = []
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.gestures = ""
        try:
            self.connect_wiimote()
        except Exception as e:
            print(e, ", no wiimote found")

        self.initUI()

    def initUI(self):
        """ ui gets defined and layouts with labels, lineEdit and buttons are added to window,
        signals for buttons are set"""
        layout = QtWidgets.QVBoxLayout()
        layoutSettings = QtWidgets.QHBoxLayout()
        layoutAdded = QtWidgets.QHBoxLayout()
        self.setWindowTitle("§1 Gesture Recognizer")
        label1 = QtWidgets.QLabel("Add new gesture:")
        layoutSettings.addWidget(label1)
        self.name_gesture = QtWidgets.QLineEdit()
        self.name_gesture.setPlaceholderText("Type name..")
        self.name_gesture.setStyleSheet("border: 1px solid grey")
        self.name_gesture.textChanged.connect(self.text_changed)
        layoutSettings.addWidget(self.name_gesture)

        self.add_button = QtWidgets.QPushButton("add new gesture")
        layoutSettings.addWidget(self.add_button)
        self.add_button.setStyleSheet("background-color: white")
        self.add_button.setEnabled(False)
        self.add_button.clicked.connect(self.clicked_button)

        label2 = QtWidgets.QLabel("Recognize gesture:")
        layoutSettings.addWidget(label2)

        self.recognize_button = QtWidgets.QPushButton("recognize gesture")
        layoutSettings.addWidget(self.recognize_button)
        self.recognize_button.setEnabled(False)
        self.recognize_button.setStyleSheet("background-color: white")
        self.recognize_button.clicked.connect(self.clicked_button)

        self.showGestures = QtWidgets.QLabel("")
        layoutAdded.addWidget(self.showGestures)
        self.labelRecognize = QtWidgets.QLabel("")
        layoutAdded.addWidget(self.labelRecognize)
        self.labelRecognize.setAlignment(QtCore.Qt.AlignRight)
        layout.setAlignment(QtCore.Qt.AlignBottom)
        layoutAdded.setAlignment(QtCore.Qt.AlignBottom)
        layout.addLayout(layoutSettings)
        layout.addLayout(layoutAdded)
        self.window().setLayout(layout)
        self.show()

    def text_changed(self):
        """when text is written for adding gesture, button for adding is enabled"""
        self.add_button.setEnabled(True)

    def ctrlWidget(self):
        return self.ui

    def clicked_button(self):
        """when a button is clicked it is controlled which button is pressed and the drawn gesture is given to recognizer
        depending on add or recognize button"""
        if len(self.pos) is not 0 and self.name_gesture.text() is not "":
            if self.sender().text() == self.add_button.text():
                self.recognizer.addTitleGesture(self.name_gesture.text())
                self.recognizer.addGesture(self.pos)
                if self.gestures is "":
                    self.gestures = self.name_gesture.text()
                else:
                    self.gestures = self.gestures + ", " + self.name_gesture.text()
                self.showGestures.setText(self.gestures)
                self.name_gesture.setText("")
                self.name_gesture.setPlaceholderText("Type name...")
                self.recognize_button.setEnabled(True)
                self.add_button.setEnabled(False)
        if self.sender().text() == self.recognize_button.text():
            self.recognizer.recognizeGesture(self.pos)
            text = self.recognizer.getGestureName()
            if text == "gesture not found":
                self.labelRecognize.setStyleSheet("color: red")
                self.labelRecognize.setText(text)
            else:
                self.labelRecognize.setStyleSheet("color: green")
                self.labelRecognize.setText(text)

    def connect_wiimote(self):
        """tries to connect to wiimote, start transform the wiimote data and
        a callback is set for catching button press "A" on the wiimote"""
        self.wm = wiimote.connect("18:2A:7B:F3:F8:F5")

        if self.wm is not None:
            self.wm.ir.register_callback(self.process_wiimote_ir_data)
            self.wm.buttons.register_callback(self.getButton)

    def getButton(self, event):
        """when a button on the wiimote is pressed it is controlled if this was "A" and
        during pressing "A" all positions are added to positions for drawing and recognizing"""
        if self.wm.buttons["A"]:
            if self.draw is False:
                self.pos = []
                self.update()
            self.draw = True
            if self.draw:
                x = self.cursor().pos().x()
                y = self.cursor().pos().y()
                self.pos.append((x, y))
                self.update()
        else:
            self.draw = False

    def process_wiimote_ir_data(self, event):
        """ the center of the wiimote led camera is transformed to
        the cursor on the screen"""
        if len(event) == 4:
            leds = []

            for led in event:
                leds.append((led["x"], led["y"]))

            if leds[0][0] == leds[0][1] == leds[1][0] == leds[1][1] == leds[2][0] \
                    == leds[2][1] == leds[3][0] == leds[3][1]:
                return -1, -1

            P, DEST_W, DEST_H = (1024 / 2, 768 / 2), 1280, 676

            x, y = self.transformer.transform(P, leds, DEST_W, DEST_H)

            self.cursor().setPos(self.mapToGlobal(QtCore.QPoint(x, y)))

    def mousePressEvent(self, event):
        """when the left button on the mouse is pressed, the bool for drawing is set true and points are set to None,
        so that a new gesture can be drawn"""
        if event.button() == QtCore.Qt.LeftButton:
            self.draw = True
            self.pos = []
            self.update()

    def mouseMoveEvent(self, event):
        """while bool for drawing is true the position of the mouse cursor during moving are added to points"""
        if self.draw:
            point = (event.x(), event.y())
            self.pos.append(point)
            self.update()

    def paintEvent(self, event):
        """the cursor movement is drawn if bool for drawing is true"""
        self.qp.begin(self)
        if len(self.pos) > 1:
            for i in range(len(self.pos)-1):
                self.qp.drawLine(self.pos[i][0], self.pos[i][1], self.pos[i+1][0], self.pos[i+1][1])
        self.qp.end()

    def mouseReleaseEvent(self, event):
        """when mouse is released the bool draw is set false"""
        if event.button() == QtCore.Qt.LeftButton:
            self.draw = False
            self.update()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
