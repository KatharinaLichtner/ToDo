#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

import wiimote
from recognizer import Recognizer
from transform import Transform
from PyQt5 import QtWidgets, QtCore, QtGui
from pylab import *
from scipy import fft
from sklearn import svm
import numpy as np
import sys
import activity


class DrawWidget(QtWidgets.QWidget):
    def __init__(self, parent):
        super(DrawWidget, self).__init__()

        self.setMouseTracking(True)
        self.qp = QtGui.QPainter()
        self.pos = []
        self.draw = False
        self.parent = parent

    def mousePressEvent(self, event):
        """when the left button on the mouse is pressed, the bool for drawing is set true and points are set to None,
        so that a new gesture can be drawn"""
        if event.button() == QtCore.Qt.LeftButton:
            self.draw = True
            self.raise_()

        self.update()

    def mouseMoveEvent(self, event):
        """while bool for drawing is true the position of the mouse cursor during moving are added to points"""
        if self.draw:
            point = (event.x(), event.y())
            print("P", point)
            self.pos.append(point)
            self.update()

    def paintEvent(self, event):
        """the cursor movement is drawn if bool for drawing is true"""
        self.qp.begin(self)
        self.qp.setPen(QtGui.QColor(255,105,180))
        if len(self.pos) > 1:
            for i in range(len(self.pos)-1):
                self.qp.drawLine(self.pos[i][0], self.pos[i][1], self.pos[i+1][0], self.pos[i+1][1])
        self.qp.end()

    def mouseReleaseEvent(self, event):
        """when mouse is released the bool draw is set false"""
        if len(self.pos) == 0:
            print("no gesture made")
        else:
            if event.button() == QtCore.Qt.LeftButton:
                self.draw = False
                self.parent.raiseWidgets()
                self.update()

class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.btaddr = "B8:AE:6E:1B:AD:A0"
        self.wiimote = None
        self._acc_vals = []
        self._bufferX = np.array([])
        self._bufferY = np.array([])
        self._bufferZ = np.array([])
        self._avg = np.array([])
        self.predicted = -1
        self.buttonA = False
        self.moveOneUp = False
        self.moveOneDown = False
        self.moveCompleteDown = False
        self.moveCompleteUp = False

        self.featureVector = activity.TrainingData.featureVector
        self.trainingDataTest = activity.TrainingData.trainingDataTest

        self.trainingData = []
        self.trainingData.append(self.trainingDataTest)
        self.c = svm.SVC()
        self.fourier = []
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_all_sensors)

        try:
            self.connect_wiimote()
        except Exception as e:
            print(e, ", no wiimote found")

        self.initUI()

        # init status arrays for undo and redo
        self.current = []
        self.undoRedo = []
        self.undoRedoTodo = []
        self.undoRedoDone = []
        self.undoRedoIndex = -1
        self.status = ""

        self.pos = []
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.recognizer = Recognizer()
        self.transform = Transform()
        self.qp = QtGui.QPainter()
        self.draw = False

    def initUI(self):
        # init window
        self.setGeometry(0, 0, 1280, 676)
        self.setStyleSheet("background-color: white")

        self.layout = QtWidgets.QVBoxLayout()
        layoutSettings = QtWidgets.QHBoxLayout()
        self.layoutList = QtWidgets.QHBoxLayout()

        self.draw_widget = DrawWidget(self)
        self.draw_widget.setParent(self)
        self.draw_widget.setGeometry(self.x(), self.y(), self.width(), self.height())

        # layoutSettings with undo and redo buttons
        self.undoButton = QtWidgets.QPushButton("Undo")
        self.undoButton.clicked.connect(self.undo)
        self.redoButton = QtWidgets.QPushButton("Redo")
        self.redoButton.clicked.connect(self.redo)
        layoutSettings.addWidget(self.undoButton)

        layoutSettings.addWidget(self.redoButton)
        layoutSettings.setAlignment(QtCore.Qt.AlignTop)
        layoutSettings.setAlignment(QtCore.Qt.AlignRight)

        # init tabs
        self.tab = QtWidgets.QTabWidget()
        self.tabToDo = QtWidgets.QWidget()
        tabDone = QtWidgets.QWidget()
        self.tab.addTab(self.tabToDo, "To Do")
        self.tab.addTab(tabDone, "Done")
        self.layoutList.addWidget(self.tab)

        # listWidget ToDoList
        # transparent background from source https://stackoverflow.com/questions/27497209/how-to-make-a-qwidget-based-
        # window-have-a-transparent-background
        self.toDoList = QtWidgets.QListWidget()
        layoutListToDoWidget = QtWidgets.QHBoxLayout()

        layoutListToDoWidget.addWidget(self.toDoList)
        self.tabToDo.setLayout(layoutListToDoWidget)
        self.tabToDo.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.toDoList.setStyleSheet("QListWidget::indicator:unchecked{image: url(unchecked.svg)}")

        # listWidget DoneList
        self.doneList = QtWidgets.QListWidget()
        self.doneList.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.doneList.setStyleSheet("QListWidget::indicator:checked{image: url(checked.svg)}")
        layoutListDoneWidget = QtWidgets.QHBoxLayout()
        layoutListDoneWidget.addWidget(self.doneList)
        tabDone.setLayout(layoutListDoneWidget)

        self.toDoList.itemClicked.connect(self.checkItemOnList)
        self.doneList.itemClicked.connect(self.checkItemOnList)

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
        self.layout.addLayout(layoutSettings)

        self.layout.addLayout(self.layoutList)
        self.window().setLayout(self.layout)
        self.show()

    def connect_wiimote(self):
        self.wiimote = wiimote.connect(self.btaddr)

        if self.wiimote is not None:
            self.wiimote.ir.register_callback(self.process_wiimote_ir_data)
            self.wiimote.buttons.register_callback(self.getPressedButton)
            self.set_update_rate(30)

    # gets which button was pressed on the wiimote
    def getPressedButton(self, ev):
        #self.predicted = -1
        x = self.cursor().pos().x()
        y = self.cursor().pos().y()
        getCurrentTab = self.tab.currentIndex()
        #print("aktueller Tab", getCurrentTab)


        # if the undo or the redo buttons were clicked while pressing the 'A'-Button on the wiimote, the action is
        if self.wiimote.buttons["A"]:

            self.buttonA = True
            xUndo = self.undoButton.pos().x()
            yUndo = self.undoButton.pos().x()
            xRedo = self.redoButton.pos().x()
            yRedo = self.redoButton.pos().y()

            if x > xUndo and x < xUndo + self.undoButton.width() and y > yUndo and y < yUndo + self.undoButton.height():
                self.undo()

            elif x > xRedo and x < xRedo + self.redoButton.width() and y > yRedo and y < yRedo + self.redoButton.height():
                self.redo()
        else:
            # ToDoTab: check if 'A'-Button is released and if it was pressed before
            # if predicted activity equals shaking from the left to the right side the current item will be deleted
            # if the toDoList contains items the first item will be the current item
            if self.predicted == 0 and self.buttonA is True and getCurrentTab == 0:
                self.buttonA = False
                item = self.toDoList.currentRow()

                self.toDoList.takeItem(item)
                itemToSelect = self.toDoList.item(0)
                if itemToSelect is not None:
                    self.toDoList.setCurrentItem(itemToSelect)

            # DoneTab: check if 'A'-Button is released and if it was pressed before
            # if predicted activity equals shaking from the left to the right side the current item will be deleted
            # if the toDoList contains items the first item will be the current item
            if self.predicted == 0 and self.buttonA is True and getCurrentTab == 1:
                self.buttonA = False
                item = self.doneList.currentRow()

                self.doneList.takeItem(item)
                itemToSelect = self.doneList.item(0)
                if itemToSelect is not None:
                    self.doneList.setCurrentItem(itemToSelect)

        # if the 'Plus'-Button is released an the wiimote is not moving the current item will be moved up by one element
        if self.wiimote.buttons['Plus'] and self.predicted == 2:
            self.moveOneUp = True
        else:

            itemTodo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemTodo is not None and itemTodo >= 0 and self.moveOneUp is True and getCurrentTab == 0:
                self.moveOneUp = False
                newitempos = itemTodo -1
                currentRow = self.toDoList.currentRow()
                currentItem = self.toDoList.takeItem(currentRow)
               # print("Um eins hoch verschieben")
                #for i in range(len(self.toDoList)):

                self.toDoList.insertItem(currentRow - 1, currentItem)
                self.toDoList.setCurrentItem(currentItem)
            elif itemDone is not None and itemDone >= 0 and self.moveOneUp is True and getCurrentTab == 1:
                self.moveOneUp = False
                newitempos = itemDone -1
                currentRow = self.doneList.currentRow()
                currentItem = self.doneList.takeItem(currentRow)
               # print("Um eins hoch verschieben")
                #for i in range(len(self.toDoList)):

                self.doneList.insertItem(currentRow - 1, currentItem)
                self.doneList.setCurrentItem(currentItem)

         # if the 'Minus'-Button is released an the wiimote is not moving the current item will be moved down by one element
        if self.wiimote.buttons['Minus'] and self.predicted == 2:
            print("ein nach unten")
            self.moveOneDown = True
        else:

            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None and itemToDo >= 0 and self.moveOneDown is True and getCurrentTab == 0:
                self.moveOneDown = False
                newitempos = itemToDo -1
                currentRow = self.toDoList.currentRow()
                currentItem = self.toDoList.takeItem(currentRow)
                self.toDoList.insertItem(currentRow + 1, currentItem)
                self.toDoList.setCurrentItem(currentItem)
            elif itemDone is not None and itemDone >= 0 and self.moveOneDown is True and getCurrentTab == 1:
                self.moveOneDown = False
                newitempos = itemDone -1
                currentRow = self.doneList.currentRow()
                currentItem = self.doneList.takeItem(currentRow)
                self.doneList.insertItem(currentRow + 1, currentItem)
                self.doneList.setCurrentItem(currentItem)


        # if the 'Plus'-Button is released an the wiimote is moved in the shape of a infinity symbol the current item will be moved to the bottom of the list
        if self.wiimote.buttons['Plus'] and self.predicted == 1:
            print("ganz nach oben")
            self.moveCompleteUp = True
        else:

            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None and itemToDo >= 0 and self.moveCompleteUp is True and getCurrentTab == 0:
                self.moveCompleteUp = False
                #newitempos = len(self.toDoList)
                currentRow = self.toDoList.currentRow()
                currentItem = self.toDoList.takeItem(currentRow)
               # print("Um eins hoch verschieben")
                #for i in range(len(self.toDoList)):

                self.toDoList.insertItem(0, currentItem)
                self.toDoList.setCurrentItem(currentItem)

            elif itemDone is not None and itemDone >= 0 and self.moveCompleteUp is True and getCurrentTab == 1:
                self.moveCompleteUp = False
                #newitempos = len(self.toDoList)
                currentRow = self.doneList.currentRow()
                currentItem = self.doneList.takeItem(currentRow)
               # print("Um eins hoch verschieben")
                #for i in range(len(self.toDoList)):

                self.doneList.insertItem(0, currentItem)
                self.doneList.setCurrentItem(currentItem)

        # if the 'Minus'-Button is released an the wiimote is moved in the shape of a infinity symbol the current item will be moved to the top of the list
        if self.wiimote.buttons['Minus'] and self.predicted == 1:
            print("ganz nach unten")
            self.moveCompleteDown = True
        else:

            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None and itemToDo >= 0 and self.moveCompleteDown is True:
                self.moveCompleteDown = False
                newitempos = len(self.toDoList)
                currentRow = self.toDoList.currentRow()
                currentItem = self.toDoList.takeItem(currentRow)

                self.toDoList.insertItem(newitempos, currentItem)
                self.toDoList.setCurrentItem(currentItem)

            elif itemDone is not None and itemDone >= 0 and self.moveCompleteDown is True:
                self.moveCompleteDown = False
                newitempos = len(self.doneList)
                currentRow = self.doneList.currentRow()
                currentItem = self.doneList.takeItem(currentRow)

                self.doneList.insertItem(newitempos, currentItem)
                self.doneList.setCurrentItem(currentItem)


        self.update()

    # sets the status of the window to one status backwards
    def undo(self):
        self.undoRedoIndex -= 1
        self.undoRedoTodoList()
        self.undoRedoDoneList()
        self.status = "undo"

    # sets the status of the window to one status forward
    def redo(self):
        if self.undoRedoIndex + 1 <= -1:
            self.undoRedoIndex += 1
        self.undoRedoTodoList()
        self.undoRedoDoneList()


    # sets the to do list to a new state
    def undoRedoTodoList(self):
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoTodo = self.undoRedo[self.undoRedoIndex][0][:]
        else:
            self.undoRedoTodo = []
        self.toDoList.clear()
        for i in range(len(self.undoRedoTodo)):
            if len(self.undoRedoTodo) is not 0:
                item = QtWidgets.QListWidgetItem(self.undoRedoTodo[i])
                item.setCheckState(0)
                self.toDoList.insertItem(0, item)
        self.toDoList.show()

    def undoRedoDoneList(self):
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoDone = self.undoRedo[self.undoRedoIndex][1][:]
        else:
            self.undoRedoDone = []
        self.doneList.clear()
        for i in range(len(self.undoRedoDone)):
            if len(self.undoRedoDone) is not 0:
                item = QtWidgets.QListWidgetItem(self.undoRedoDone[i])
                item.setCheckState(0)
                self.doneList.insertItem(0, item)
                self.doneList.show()

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
        #print("accelerometer", self._acc_vals, "x", x, "y", y, "z", z)

        fftData = self.fft(x, y, z)
        self.fourier.append(fftData)
        if len(self.fourier) >= 32:
            self.svm(fftData)
            self.update()

    # fft reads in the accelerometer data of x-,y- and z-axis.
    # calculate the peaks of the raw data from every movement with the furier transformations
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
        #print("Predicted", self.predicted)


    def update_accel(self, acc_vals):
        self._acc_vals = acc_vals

    def process_wiimote_ir_data(self,event):
        if len(event) == 4:
            leds = []

            for led in event:
                leds.append((led["x"], led["y"]))

            if leds[0][0] == leds[0][1] == leds[1][0] == leds[1][1] == leds[2][0] \
                    == leds[2][1] == leds[3][0] == leds[3][1]:
                return -1, -1

            P, DEST_W, DEST_H = (1024 / 2, 768 / 2), 1280, 676
            try:
                x, y = self.transform.transform(P, leds, DEST_W, DEST_H)
            except Exception as e:
                print(e)
                x = y = -1

            self.cursor().setPos(self.mapToGlobal(QtCore.QPoint(x, y)))

    def mousePressEvent(self, event):
        """when the left button on the mouse is pressed, the bool for drawing is set true and points are set to None,
        so that a new gesture can be drawn"""
        if event.button() == QtCore.Qt.RightButton:
            self.draw = True
            self.draw_widget.activateWindow()
            self.draw_widget.raise_()

        self.update()


    def mouseMoveEvent(self, event):
        """while bool for drawing is true the position of the mouse cursor during moving are added to points"""
        if self.draw:
            point = (event.x(), event.y())
            self.pos.append(point)
            #self.update()

    def paintEvent(self, event):
        """the cursor movement is drawn if bool for drawing is true"""
        self.qp.begin(self)
        self.qp.setPen(QtGui.QColor(255,105,180))
        if len(self.pos) > 1:
            for i in range(len(self.pos)-1):
                self.qp.drawLine(self.pos[i][0], self.pos[i][1], self.pos[i+1][0], self.pos[i+1][1])
        self.qp.end()

    def mouseReleaseEvent(self, event):
        """when mouse is released the bool draw is set false"""
        if len(self.pos) == 0:
            print("no gesture made")
        else:
            if event.button() == QtCore.Qt.RightButton:
                self.draw = False
                self.undoButton.raise_()
                self.redoButton.raise_()
                self.tab.raise_()
                self.tabToDo.raise_()
                self.toDoList.raise_()
                recognized = self.recognizer.recognizeGesture(self.pos)
                self.recognizedAction(recognized)
                self.pos = []
                self.update()

    def raiseWidgets(self):
        self.undoButton.raise_()
        self.redoButton.raise_()
        self.tab.raise_()
        self.tabToDo.raise_()
        self.toDoList.raise_()

    # takeItem from source: https://stackoverflow.com/questions/23835847/how-to-remove-item-from-qlistwidget/23836142
    def recognizedAction(self, recognized):
        if recognized == "Circle":
            self.editToDo.setFocus()
            self.inputToDo.show()
        elif recognized == "Check":
            if self.toDoList.currentItem() is not None:
                item = self.toDoList.currentItem()
                self.toDoList.takeItem(self.toDoList.row(item))
                newItem = QtWidgets.QListWidgetItem(item.text())
                newItem.setCheckState(2)
                self.doneList.insertItem(0, newItem)
                self.doneList.setCurrentItem(newItem)
        elif recognized == "Uncheck":
            if self.doneList.currentItem() is not None:
                item = self.doneList.currentItem()
                self.doneList.takeItem(self.doneList.row(item))
                newItem = QtWidgets.QListWidgetItem(item.text())
                newItem.setCheckState(0)
                newItem.checkState()
                self.toDoList.insertItem(0, newItem)
                self.toDoList.setCurrentItem(newItem)

    def checkItemOnList(self, item):
        if item.checkState() == 2:
            self.toDoList.takeItem(self.toDoList.row(item))
            newItem = QtWidgets.QListWidgetItem(item.text())
            newItem.setCheckState(2)
            self.doneList.insertItem(0, newItem)
            self.doneList.setCurrentItem(newItem)
        elif item.checkState() == 0:
            self.doneList.takeItem(self.doneList.row(item))
            newItem = QtWidgets.QListWidgetItem(item.text())
            newItem.setCheckState(0)
            newItem.checkState()
            self.toDoList.insertItem(0, newItem)
            self.toDoList.setCurrentItem(newItem)

    def getNewEntry(self):
        if self.sender().text() == self.okButton.text():
            self.newEntry = self.editToDo.text()
            self.undoRedoTodo.append(self.newEntry)
            self.current = []
            self.current.append(self.undoRedoTodo[:])
            self.current.append(self.undoRedoDone[:])
            if self.status == "undo":
                self.undoRedo = self.undoRedo[:self.undoRedoIndex + 1][:]
                self.undoRedoIndex = -1
                self.status = ""
            self.undoRedo.append(self.current[:])
            self.editToDo.setText("")
            self.inputToDo.hide()
            item = QtWidgets.QListWidgetItem(self.newEntry)
            item.setCheckState(0)
            self.toDoList.insertItem(0, item)
            self.toDoList.setCurrentItem(item)
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
