#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

import wiimote
import sys
from recognizer import Recognizer
from transform import Transform
from PyQt5 import QtWidgets, QtCore, QtGui


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.btaddr = "18:2A:7B:F3:F8:F5"
        self.wiimote = None
        self._acc_vals = []
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_all_sensors)
        self.initUI()
        try:
            self.connect_wiimote()
        except Exception as e:
            print(e, ", no wiimote found")

        self.pos = []
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.recognizer = Recognizer()
        self.transform = Transform()
        self.qp = QtGui.QPainter()
        self.draw = False

    def initUI(self):
        # init window
        self.setGeometry(0, 0, 640, 720)
        self.window().setStyleSheet("background-color: white")

        layout = QtWidgets.QVBoxLayout()
        layoutSettings = QtWidgets.QHBoxLayout()
        layoutList = QtWidgets.QHBoxLayout()

        # layoutSettings with undo and redo buttons
        self.undoButton = QtWidgets.QPushButton("Undo")
        self.redoButton = QtWidgets.QPushButton("Redo")
        layoutSettings.addWidget(self.undoButton)
        layoutSettings.addWidget(self.redoButton)
        layoutSettings.setAlignment(QtCore.Qt.AlignTop)
        layoutSettings.setAlignment(QtCore.Qt.AlignRight)

        # init tabs
        self.tab = QtWidgets.QTabWidget()
        tabToDo = QtWidgets.QWidget()
        tabDone = QtWidgets.QWidget()
        self.tab.addTab(tabToDo, "To Do")
        self.tab.addTab(tabDone, "Done")

        # listWidget ToDoList
        self.toDoList = QtWidgets.QListWidget()
        layoutListToDoWidget = QtWidgets.QHBoxLayout()
        layoutListToDoWidget.addWidget(self.toDoList)
        tabToDo.setLayout(layoutListToDoWidget)
        self.toDoList.setStyleSheet("background-color: white")
        self.toDoList.setStyleSheet("QListWidget::indicator:unchecked{image: url(unchecked.svg)}")

        # listWidget DoneList
        self.doneList = QtWidgets.QListWidget()
        self.doneList.setStyleSheet("background-color: white")
        self.doneList.setStyleSheet("QListWidget::indicator:checked{image: url(checked.svg)}")
        layoutListDoneWidget = QtWidgets.QHBoxLayout()
        layoutListDoneWidget.addWidget(self.doneList)
        tabDone.setLayout(layoutListDoneWidget)

        layoutList.addWidget(self.tab)

        # init Popup
        self.inputToDo = QtWidgets.QWidget()
        layoutPopup = QtWidgets.QVBoxLayout()
        layoutInput = QtWidgets.QVBoxLayout()
        layoutButtons = QtWidgets.QHBoxLayout()
        self.inputToDo.setWindowTitle("New To Do")
        labelInput = QtWidgets.QLabel("Type in new To Do:")
        self.editToDo = QtWidgets.QLineEdit()
        self.editToDo.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.okButton = QtWidgets.QPushButton("OK")
        self.okButton.clicked.connect(self.getNewEntry)
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.getNewEntry)
        layoutInput.addWidget(labelInput)
        layoutInput.addWidget(self.editToDo)
        layoutButtons.addWidget(self.cancelButton)
        layoutButtons.addWidget(self.okButton)
        layoutButtons.setAlignment(QtCore.Qt.AlignBottom)
        layoutPopup.addLayout(layoutInput)
        layoutPopup.addLayout(layoutButtons)
        self.inputToDo.setLayout(layoutPopup)

        # adding layouts tab und Settings to window
        layout.addLayout(layoutSettings)
        layout.addLayout(layoutList)
        self.window().setLayout(layout)
        self.toDoList.installEventFilter(self.toDoList)
        self.show()

    def eventFilter(self, widget, event):
        print(event)
        return self.toDoList.eventFilter(self.toDoList, widget, event)

    def connect_wiimote(self):
        if self.wiimote is not None:
            self.wiimote.disconnect()
            self.wiimote = None
            print("connect")
            return
        if len(self.btaddr) == 17:
            print("connecting")
            self.wiimote = wiimote.connect(self.btaddr)
            if self.wiimote is None:
                print("try again")
            else:
                print("disconnect")
                self.set_update_rate(30)

    def set_update_rate(self, rate):
        if rate == 0:  # use callbacks for max. update rate
            self.update_timer.stop()
            self.wiimote.accelerometer.register_callback(self.update_accel)
        else:
            self.wiimote.accelerometer.unregister_callback(self.update_accel)
            self.update_timer.start(1000.0/rate)

    def update_all_sensors(self):
        if self.wiimote is None:
            return
        self._acc_vals = self.wiimote.accelerometer
        x, y, z = self._acc_vals
        print("accelerometer", self._acc_vals, "x", x, "y", y, "z", z)
        # todo: other sensors...
        self.update()

    def update_accel(self, acc_vals):
        self._acc_vals = acc_vals
        self.update()

    def process_wiimote_ir_data(self,event):
        if len(event) == 4:
            leds = []

            for led in event:
                leds.append((led["x"], led["y"]))
            P, DEST_W, DEST_H = (1024 /2, 768/2), 1280, 676

            try:
                x, y = self.transform.transform(P, leds, DEST_W, DEST_H)
            except Exception as e:
                print(e)
                x = y = -1

            self.cursor().setPos(self.mapToGlobal(QtCore.QPoint(x,y)))

    def mousePressEvent(self, event):
        """when the left button on the mouse is pressed, the bool for drawing is set true and points are set to None,
        so that a new gesture can be drawn"""
        if event.button() == QtCore.Qt.LeftButton:
            self.draw = True
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
            recognized = self.recognizer.recognizeGesture(self.pos)
            self.recognizedAction(recognized)
            self.pos = []
            self.update()

    def recognizedAction(self, recognized):
        if recognized == 0:
            self.inputToDo.show()
        if recognized == 1:
            # get selected Item, remove and add to donelist
            item = self.toDoList.currentItem()
            self.toDoList.removeItemWidget(item)
            item.setCheckState(2)
            self.doneList.addItem(item)
            self.update()

    def getNewEntry(self):
        if self.sender().text() == self.okButton.text():
            self.newEntry = self.editToDo.text()
            self.editToDo.setText("")
            self.inputToDo.hide()
            item = QtWidgets.QListWidgetItem(self.newEntry)
            item.setCheckState(0)
            self.toDoList.insertItem(0, item)
        elif self.sender().text() == self.cancelButton.text():
            self.inputToDo.hide()


def main():
    app = QtWidgets.QApplication(sys.argv)
    font_db = QtGui.QFontDatabase()
    font_id = font_db.addApplicationFont("Handlee-Regular.ttf")
    handleeFont = QtGui.QFont("Handlee")
    app.setFont(handleeFont)
    w = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
