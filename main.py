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

    def drawOnWidget(self, draw):
        if draw:
            self.draw = draw
            self.update()
        else:
            self.draw = False
            self.parent.recognizeDrawing(self.pos)
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
        if self.draw:
            self.qp.begin(self)
            self.qp.setPen(QtGui.QColor(255, 105, 180))
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
                self.parent.recognizeDrawing(self.pos)
                self.pos = []
                self.update()

class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.btaddr = "18:2A:7B:F3:F8:F5"
        #self.btaddr = "B8:AE:6E:1B:AD:A0"
        #self.btaddr = "B8:AE:6E:50:05:32"

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

        self.arrowUp = False
        self.arrowDown = False

        self.btn_One = False
        self.btn_Two = False


        self.featureVector = activity.TrainingData.featureVector
        self.trainingDataTest = activity.TrainingData.trainingDataTest

        self.trainingData = []
        self.trainingData.append(self.trainingDataTest)
        self.c = svm.SVC()
        self.fourier = []
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_all_sensors)

        # init status arrays for undo and redo
        self.current = []
        self.undoRedo = [[[],[]]]
        self.undoRedoTodo = []
        self.undoRedoDone = []
        self.undoRedoIndex = -1
        self.status = ""
        self.undoRedoLength = 5
        self.editIndex = 0

        self.pos = []
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.recognizer = Recognizer()
        self.transform = Transform()
        self.qp = QtGui.QPainter()
        self.draw = False
        self.tabIndex = 0
        self.initUI()

        try:
            self.connect_wiimote()
        except Exception as e:
            print(e, ", no wiimote found")

    def initUI(self):
        # init window

        self.setGeometry(0, 0, 1280, 800)
        #self.setGeometry(0, 0, 1920, 950)

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
        self.deleteButton = QtWidgets.QPushButton("Delete")
        self.newItemButton = QtWidgets.QPushButton("New Item")
        self.deleteButton.clicked.connect(self.delete)
        self.newItemButton.clicked.connect(self.addnewItem)
        layoutSettings.addWidget(self.deleteButton)
        layoutSettings.addWidget(self.newItemButton)
        layoutSettings.addWidget(self.undoButton)

        layoutSettings.addWidget(self.redoButton)
        layoutSettings.setAlignment(QtCore.Qt.AlignTop)
        layoutSettings.setAlignment(QtCore.Qt.AlignRight)

        # init tabs
        self.tab = QtWidgets.QTabWidget()
        self.tabToDo = QtWidgets.QWidget()
        self.tabDone = QtWidgets.QWidget()
        self.tab.addTab(self.tabToDo, "To Do")
        self.tab.addTab(self.tabDone, "Done")
        self.layoutList.addWidget(self.tab)

        # listWidget ToDoList
        # transparent background from source https://stackoverflow.com/questions/27497209/how-to-make-a-qwidget-based-
        # window-have-a-transparent-background
        self.toDoList = QtWidgets.QListWidget()
        self.toDoList.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.toDoList.setStyleSheet("QListView::item:selected{background-color: pink}")
        #self.toDoList.setStyleSheet("QListView::item {color: black}")


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
        self.tabDone.setLayout(layoutListDoneWidget)


        self.toDoList.itemClicked.connect(self.checkItemOnToDoList)
        self.doneList.itemClicked.connect(self.checkItemOnDoneList)


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
        self.inputToDo.installEventFilter(self)

        self.editItems = QtWidgets.QWidget()
        layoutEditPopup = QtWidgets.QVBoxLayout()
        layoutEditInputPopup = QtWidgets.QVBoxLayout()
        layoutEditButtons = QtWidgets.QHBoxLayout()
        self.editItems.setWindowTitle("Edit Item")
        self.labelEditInput = QtWidgets.QLabel("Edit:")
        self.editInput = QtWidgets.QLineEdit()
        self.editInput.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.okEditButton = QtWidgets.QPushButton("OK")
        self.okEditButton.clicked.connect(self.getEditEntry)
        self.cancelEditButton = QtWidgets.QPushButton("Cancel")
        self.cancelEditButton.clicked.connect(self.getEditEntry)
        layoutEditInputPopup.addWidget(self.labelEditInput)
        layoutEditInputPopup.addWidget(self.editInput)
        layoutEditButtons.addWidget(self.cancelEditButton)
        layoutEditButtons.addWidget(self.okEditButton)
        layoutEditButtons.setAlignment(QtCore.Qt.AlignBottom)
        layoutEditPopup.addLayout(layoutEditInputPopup)
        layoutEditPopup.addLayout(layoutEditButtons)
        self.editItems.setLayout(layoutEditPopup)
        self.editItems.installEventFilter(self)

        # adding layouts tab und Settings to window
        self.layout.addLayout(layoutSettings)

        self.layout.addLayout(self.layoutList)
        self.setLayout(self.layout)
        self.show()

    def connect_wiimote(self):
        self.wiimote = wiimote.connect(self.btaddr)

        if self.wiimote is not None:
            self.wiimote.ir.register_callback(self.process_wiimote_ir_data)
            self.wiimote.buttons.register_callback(self.getPressedButton)
            self.set_update_rate(10)

    # gets which button was pressed on the wiimote
    def getPressedButton(self, ev):
        x = self.cursor().pos().x()
        y = self.cursor().pos().y()
        getCurrentTab = self.tab.currentIndex()

        if self.wiimote.buttons["B"]:
            self.draw_widget.raise_()
            if not self.draw:
                self.pos = []

            self.draw = True

            self.draw_widget.drawOnWidget(self.draw)

        else:
            self.draw = False
            self.draw_widget.drawOnWidget(self.draw)


        # if the undo or the redo buttons were clicked while pressing the 'A'-Button on the wiimote, the action is
        if self.wiimote.buttons["A"]:

            self.buttonA = True

        else:
            if self.buttonA is True:
                xUndo = self.undoButton.pos().x()
                yUndo = self.undoButton.pos().y()
                xRedo = self.redoButton.pos().x()
                yRedo = self.redoButton.pos().y()
                xDelete = self.deleteButton.pos().x()
                yDelete = self.deleteButton.pos().y()
                xaddItem = self.newItemButton.pos().x()
                yaddItem = self.newItemButton.pos().y()
                xItems = self.editItems.pos().x()
                yItems = self.editItems.pos().y()
                xEdit = self.okEditButton.pos().x()
                yEdit = self.okEditButton.pos().y()
                xEditCancel = self.cancelEditButton.pos().x()
                yEditCancel = self.cancelEditButton.pos().y()
                xInput = self.inputToDo.pos().x()
                yInput = self.inputToDo.pos().y()
                xAdd = self.okButton.pos().x()
                yAdd = self.okButton.pos().y()
                xAddCancel = self.cancelButton.pos().x()
                yAddCancel = self.cancelButton.pos().y()

                if x >= xUndo and x <= xUndo + self.undoButton.width() and y >= yUndo and y <= yUndo + self.undoButton.height():
                    self.buttonA = False
                    print("undo")
                    self.undo()

                elif x >= xRedo and x <= xRedo + self.redoButton.width() and y >= yRedo and y <= yRedo + self.redoButton.height():
                    self.buttonA = False
                    print("redo")
                    self.redo()

                elif x >= xDelete and x <= xDelete + self.deleteButton.width() and y >= yDelete and y <= yDelete + self.deleteButton.height():
                    print("delete")
                    self.buttonA = False
                    self.delete()

                elif x >= xaddItem and x <= xaddItem + self.newItemButton.width() and y >= yaddItem and y <= yaddItem + self.newItemButton.height():
                    print("addItem")
                    self.buttonA = False
                    self.addnewItem()
                elif self.editItems.isVisible() and x >= xEdit + xItems and x <= xEdit + self.okEditButton.width() + xItems and y >= yEdit + yItems and y <= yEdit + self.okEditButton.height() + yItems:
                    self.buttonA = False
                    self.addEditEntry()
                elif self.editItems.isVisible() and x >= xEditCancel + xItems and x <= xEditCancel + self.cancelEditButton.width() + xItems and y >= yEditCancel + yItems and y <= yEditCancel + self.cancelEditButton.height() + yItems:
                    self.buttonA = False
                    self.editItems.hide()
                elif self.inputToDo.isVisible() and x >= xAdd + xInput and x <= xAdd + self.okButton.width() + xInput and y >= yAdd + yInput and y <= yAdd + self.okButton.height() + yInput:
                    self.buttonA = False
                    self.addNewEntry()
                    self.editInput.setText("")
                elif self.inputToDo.isVisible() and x >= xAddCancel + xInput and x <= xAddCancel + self.cancelButton.width() + xInput and y >= yAddCancel + yInput and y <= yAddCancel + self.cancelButton.height() + yInput:
                    self.buttonA = False
                    self.inputToDo.hide()
                    self.editToDo.setText("")

                else:
                    self.deleteSelectedItem(getCurrentTab)


        # if the 'Plus'-Button is released an the wiimote is not moving the current item will be moved up by one element
        if self.wiimote.buttons['Plus'] and self.predicted == 2:
            self.moveOneUp = True
        else:
            self.moveItemOneUp(getCurrentTab)


         # if the 'Minus'-Button is released an the wiimote is not moving the current item will be moved down by one element
        if self.wiimote.buttons['Minus'] and self.predicted == 2:
            self.moveOneDown = True
        else:
            self.moveItemOneDown(getCurrentTab)

        # if the 'Plus'-Button is released an the wiimote is moved in the shape of a infinity symbol the current item will be moved to the bottom of the list
        if self.wiimote.buttons['Plus'] and self.predicted == 1:
            self.moveCompleteUp = True
        else:
            self.moveItemToTop(getCurrentTab)

        # if the 'Minus'-Button is released an the wiimote is moved in the shape of a infinity symbol the current item will be moved to the top of the list
        if self.wiimote.buttons['Minus'] and self.predicted == 1:

            # print("ganz nach unten")
            self.moveCompleteDown = True
        else:
            self.moveItemToBottom(getCurrentTab)

        if self.wiimote.buttons['Up']:
            print("Pfeil nach oben")
            self.arrowUp = True
        else:
            self.arrowUpReleased(getCurrentTab)
        if self.wiimote.buttons['Down']:
            print("Pfeil nach unten")
            self.arrowDown = True
        else:
            self.arrowDownReleased(getCurrentTab)

        if self.wiimote.buttons['One']:
            self.btn_One = True
        else:
            if self.tab.currentIndex() is not 0 and self.btn_One is True:
                self.tab.setCurrentIndex(0)
                self.btn_One = False
        if self.wiimote.buttons['Two']:
            self.btn_Two = True
        else:
            if self.tab.currentIndex() is not 1 and self.btn_Two == True:
                self.tab.setCurrentIndex(1)
                self.btn_Two = False

        self.update()

    def deleteSelectedItem(self, getCurrentTab):
        # ToDoTab: check if 'A'-Button is released and if it was pressed before
        # if predicted activity equals shaking from the left to the right side the current item will be deleted
        # if the toDoList contains items the first item will be the current item
        if self.predicted == 0 and self.buttonA is True and getCurrentTab == 0:
            self.buttonA = False
            try:
                item = self.toDoList.currentRow()

                if item is not -1:
                    del self.undoRedoTodo[item]
                    self.undoRedoUpdateLists()
                    self.toDoList.takeItem(item)

                    if len(self.toDoList) > 0:
                        # = self.toDoList.item(0)
                        #if itemToSelect is not None:
                        self.toDoList.setCurrentRow(0)

            except Exception as e:
                print("E", e)


        # DoneTab: check if 'A'-Button is released and if it was pressed before
        # if predicted activity equals shaking from the left to the right side the current item will be deleted
        # if the toDoList contains items the first item will be the current item
        if self.predicted == 0 and self.buttonA is True and getCurrentTab == 1:
            self.buttonA = False
            item = self.doneList.currentRow()

            del self.undoRedoDone[item]
            self.undoRedoUpdateLists()
            self.doneList.takeItem(item)
            itemToSelect = self.doneList.item(0)
            if itemToSelect is not None:

                self.doneList.setCurrentRow(0)

    def moveItemOneUp(self, getCurrentTab):
        itemTodo = self.toDoList.currentRow()
        itemDone = self.doneList.currentRow()

        if itemTodo is not None and itemTodo >= 0 and self.moveOneUp is True and getCurrentTab == 0:
            self.moveOneUp = False

            currentItem = self.toDoList.takeItem(itemTodo)

            del self.undoRedoTodo[itemTodo]
            self.undoRedoTodo.insert(itemTodo - 1, currentItem.text())
            self.undoRedoUpdateLists()
            self.toDoList.insertItem(itemTodo - 1, currentItem)
            self.toDoList.setCurrentItem(currentItem)

        elif itemDone is not None and itemDone >= 0 and self.moveOneUp is True and getCurrentTab == 1:
            self.moveOneUp = False
            currentItem = self.doneList.takeItem(itemDone)
            del self.undoRedoDone[itemDone]
            self.undoRedoDone.insert(itemDone - 1, currentItem.text())
            self.undoRedoUpdateLists()
            self.doneList.insertItem(itemDone - 1, currentItem)
            self.doneList.setCurrentItem(currentItem)

    def moveItemOneDown(self, getCurrentTab):
            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None and itemToDo >= 0 and self.moveOneDown is True and getCurrentTab == 0:
                self.moveOneDown = False

                currentItem = self.toDoList.takeItem(itemToDo)
                del self.undoRedoTodo[itemToDo]
                self.undoRedoTodo.insert(itemToDo + 1, currentItem.text())
                self.undoRedoUpdateLists()
                self.toDoList.insertItem(itemToDo + 1, currentItem)
                self.toDoList.setCurrentItem(currentItem)

            elif itemDone is not None and itemDone >= 0 and self.moveOneDown is True and getCurrentTab == 1:
                self.moveOneDown = False
                currentItem = self.doneList.takeItem(itemDone)
                del self.undoRedoDone[itemDone]
                self.undoRedoDone.insert(itemDone + 1, currentItem.text())
                self.undoRedoUpdateLists()
                self.doneList.insertItem(itemDone + 1, currentItem)
                self.doneList.setCurrentItem(currentItem)

    def moveItemToTop(self, getCurrentTab):
        itemToDo = self.toDoList.currentRow()
        itemDone = self.doneList.currentRow()

        if itemToDo is not None and itemToDo >= 0 and self.moveCompleteUp is True and getCurrentTab == 0:
            self.moveCompleteUp = False

            currentItem = self.toDoList.takeItem(itemToDo)
            del self.undoRedoTodo[itemToDo]
            self.undoRedoTodo.insert(0, currentItem.text())
            self.undoRedoUpdateLists()

            self.toDoList.insertItem(0, currentItem)
            self.toDoList.setCurrentItem(currentItem)

        elif itemDone is not None and itemDone >= 0 and self.moveCompleteUp is True and getCurrentTab == 1:
            self.moveCompleteUp = False

            currentItem = self.doneList.takeItem(itemDone)
            del self.undoRedoDone[itemDone]
            self.undoRedoDone.insert(0, currentItem.text())
            self.undoRedoUpdateLists()

            self.doneList.insertItem(0, currentItem)
            self.doneList.setCurrentItem(currentItem)

    def moveItemToBottom(self, getCurrentTab):

            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None and itemToDo >= 0 and self.moveCompleteDown is True and getCurrentTab == 0:

                self.moveCompleteDown = False
                newitempos = len(self.toDoList)
                currentItem = self.toDoList.takeItem(itemToDo)
                del self.undoRedoTodo[itemToDo]
                self.undoRedoTodo.insert(newitempos, currentItem.text())
                self.undoRedoUpdateLists()

                self.toDoList.insertItem(newitempos, currentItem)
                self.toDoList.setCurrentItem(currentItem)

            elif itemDone is not None and itemDone >= 0 and self.moveCompleteDown is True and getCurrentTab == 1:

                self.moveCompleteDown = False
                newitempos = len(self.doneList)
                currentItem = self.doneList.takeItem(itemDone)
                del self.undoRedoDone[itemDone]
                self.undoRedoDone.insert(newitempos, currentItem.text())
                self.undoRedoUpdateLists()
                self.doneList.insertItem(newitempos, currentItem)
                self.doneList.setCurrentItem(currentItem)

    def arrowUpReleased(self, getCurrentTab):
            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None and itemToDo >= 0 and self.arrowUp is True and getCurrentTab == 0:

                self.arrowUp = False
                currentRow = self.toDoList.currentRow()
                newRow = currentRow -1
                if currentRow > 0:
                    self.toDoList.setCurrentRow(newRow)


            elif itemDone is not None and itemDone >= 0 and self.arrowUp is True and getCurrentTab == 1:

                self.arrowUp = False
                newitempos = len(self.toDoList)
                currentRow = self.toDoList.currentRow()
                newRow = currentRow -1


                itemToSelect = self.toDoList.item(newRow)
                if currentRow > 0:
                    self.toDoList.setCurrentRow(newRow)

    def arrowDownReleased(self, getCurrentTab):
            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None and itemToDo >= 0 and self.arrowDown is True and getCurrentTab == 0:

                self.arrowDown = False
                newitempos = len(self.toDoList)
                currentRow = self.toDoList.currentRow()
                newRow = currentRow +1
                if currentRow < newitempos -1:
                    self.toDoList.setCurrentRow(newRow)


            elif itemDone is not None and itemDone >= 0 and self.arrowDown is True and getCurrentTab == 1:

                self.arrowDown = False
                newitempos = len(self.toDoList)
                currentRow = self.toDoList.currentRow()
                newRow = currentRow +1
                if currentRow < newitempos -1:
                    self.toDoList.setCurrentRow(newRow)


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
        self.status = ""


    def delete(self):
        getCurrentTab = self.tab.currentIndex()
        if getCurrentTab == 0:
            item = self.toDoList.currentRow()

            if item is not -1:
                del self.undoRedoTodo[item]
                self.undoRedoUpdateLists()
                self.toDoList.takeItem(item)
                itemToSelect = self.toDoList.item(0)
                if itemToSelect is not None:
                    self.toDoList.setCurrentRow(0)
        if getCurrentTab == 1:
            item = self.doneList.currentRow()

            del self.undoRedoDone[item]
            self.undoRedoUpdateLists()
            self.doneList.takeItem(item)
            itemToSelect = self.doneList.item(0)
            if itemToSelect is not None:

                self.doneList.setCurrentRow(0)

    def addnewItem(self):
        print("addnewitem")
        self.inputToDo.show()


    # sets the to do list to a new state
    def undoRedoTodoList(self):
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoTodo = self.undoRedo[self.undoRedoIndex][0][:]
        self.toDoList.clear()
        for i in range(len(self.undoRedoTodo)):
            if len(self.undoRedoTodo) is not 0:
                item = QtWidgets.QListWidgetItem(self.undoRedoTodo[i])
                item.setCheckState(QtCore.Qt.Unchecked)
                self.toDoList.addItem(item)
                self.toDoList.setCurrentRow(0)
        self.toDoList.show()

    # sets the done list to a new state
    def undoRedoDoneList(self):
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoDone = self.undoRedo[self.undoRedoIndex][1][:]
        self.doneList.clear()
        for i in range(len(self.undoRedoDone)):
            if len(self.undoRedoDone) is not 0:
                item = QtWidgets.QListWidgetItem(self.undoRedoDone[i])
                item.setCheckState(QtCore.Qt.Checked)
                self.doneList.addItem(item)
                self.doneList.setCurrentRow(0)
        self.doneList.show()

    # if a action like add, remove, check, uncheck was made, the tod o and undo lists are updated
    def undoRedoUpdateLists(self):
        self.current = []
        self.current.append(self.undoRedoTodo[:])
        self.current.append(self.undoRedoDone[:])
        if self.status == "undo":
            self.undoRedo = self.undoRedo[:(self.undoRedoIndex + 1)][:]
            self.undoRedoIndex = -1
            self.status = ""
        self.undoRedo.append(self.current[:])
        if len(self.undoRedo) > self.undoRedoLength:
            length = len(self.undoRedo) - self.undoRedoLength
            self.undoRedo = self.undoRedo[length:][:]

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

            P, DEST_W, DEST_H = (1024 / 2, 768 / 2), 1280, 800

            try:
                x, y = self.transform.transform(P, leds, DEST_W, DEST_H)
            except Exception as e:
                print(e)
                x = y = -1

            self.cursor().setPos(self.mapToGlobal(QtCore.QPoint(x, y)))

    def keyPressEvent(self, event):
        if event.text() == "b":
            self.toDoList.clearFocus()
            self.raiseWidgets()
            self.draw_widget.raise_()

    def eventFilter(self, widget, event):
        # source from https://stackoverflow.com/questions/20420072/use-keypressevent-to-catch-enter-or-return
        if event.type() == QtCore.QEvent.KeyPress and widget is self.inputToDo:
            if event.key() == QtCore.Qt.Key_Return:
                if self.editToDo.text() is not "":
                    self.addNewEntry()
                    return True

        if event.type() == QtCore.QEvent.KeyPress and widget is self.editItems:
            if event.key() == QtCore.Qt.Key_Return:
                if self.editInput.text() is not "":
                    self.addEditEntry()
                    return True
        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def recognizeDrawing(self, pos):
        self.pos = pos
        if len(self.pos) > 0:
            recognized = self.recognizer.recognizeGesture(self.pos)
            self.recognizedAction(recognized)

    def raiseWidgets(self):
        self.undoButton.raise_()
        self.redoButton.raise_()
        self.deleteButton.raise_()
        self.newItemButton.raise_()
        self.tab.raise_()
        self.tabToDo.raise_()
        self.toDoList.raise_()

    # takeItem from source: https://stackoverflow.com/questions/23835847/how-to-remove-item-from-qlistwidget/23836142
    def recognizedAction(self, recognized):
        self.raiseWidgets()
        if recognized == "Circle":
            self.editToDo.setFocus()
            self.inputToDo.show()
        elif recognized == "Check":
            if self.toDoList.currentItem() is not None and self.tab.currentIndex() == 0:
                item = self.toDoList.currentItem()
                self.undoRedoDone.append(item.text())
                del self.undoRedoTodo[self.toDoList.row(item)]
                self.undoRedoUpdateLists()
                self.toDoList.takeItem(self.toDoList.row(item))
                newItem = QtWidgets.QListWidgetItem(item.text())
                newItem.setCheckState(QtCore.Qt.Checked)
                self.doneList.insertItem(0, newItem)
                self.doneList.setCurrentItem(newItem)
        elif recognized == "Uncheck":
            if self.doneList.currentItem() is not None:
                item = self.doneList.currentItem()
                self.undoRedoTodo.append(item.text())
                del self.undoRedoDone[self.toDoList.row(item)]
                self.undoRedoUpdateLists()
                self.doneList.takeItem(self.doneList.row(item))
                newItem = QtWidgets.QListWidgetItem(item.text())
                newItem.setCheckState(QtCore.Qt.Unchecked)
                self.toDoList.insertItem(0, newItem)
                self.toDoList.setCurrentItem(newItem)
        elif recognized == "Edit":
            self.tabIndex = self.tab.currentIndex()
            if self.tabIndex == 0:
                self.editInput.setText(self.toDoList.currentItem().text())
                self.editIndex = self.toDoList.currentRow()
                del self.undoRedoTodo[self.editIndex]
                self.editItems.show()
            if self.tabIndex == 1:
                self.editInput.setText(self.doneList.currentItem().text())
                self.editIndex = self.doneList.currentRow()
                del self.undoRedoDone[self.editIndex]
                self.editItems.show()

    def checkItemOnToDoList(self, item):

        if item.checkState() == QtCore.Qt.Checked:
            self.toDoList.takeItem(self.toDoList.row(item))
            newItem = QtWidgets.QListWidgetItem(item.text())
            newItem.setCheckState(QtCore.Qt.Checked)
            self.doneList.insertItem(0, newItem)
            self.doneList.setCurrentItem(newItem)

        else:
            pass

    def checkItemOnDoneList(self, item):
        if item.checkState() == QtCore.Qt.Unchecked:
            self.doneList.takeItem(self.doneList.row(item))
            newItem = QtWidgets.QListWidgetItem(item.text())
            newItem.setCheckState(QtCore.Qt.Unchecked)
            self.toDoList.insertItem(0, newItem)
            self.toDoList.setCurrentItem(newItem)
        else:
            pass

    def addNewEntry(self):
        self.newEntry = self.editToDo.text()
        self.undoRedoTodo.insert(0, self.newEntry)
        self.undoRedoUpdateLists()
        if self.status == "undo":
            self.undoRedo = self.undoRedo[:self.undoRedoIndex + 1][:]
            self.undoRedoIndex = -1
            self.status = ""
        self.editToDo.setText("")
        self.inputToDo.hide()
        item = QtWidgets.QListWidgetItem(self.newEntry)
        item.setCheckState(QtCore.Qt.Unchecked)
        self.toDoList.insertItem(0, item)
        self.toDoList.setCurrentItem(item)
        if self.tab.currentIndex() is not 0:
            self.tab.setCurrentIndex(0)

    def getNewEntry(self):
        if self.sender().text() == self.okButton.text():
            if self.editToDo.text() is not "":
                self.addNewEntry()
        elif self.sender().text() == self.cancelButton.text():
            self.inputToDo.hide()
            self.editToDo.setText("")

    def addEditEntry(self):
        self.editEntry = self.editInput.text()
        self.editInput.setText("")
        self.editItems.hide()
        if self.tabIndex == 0:
            self.toDoList.currentItem().setText(self.editEntry)
            self.undoRedoTodo.insert(self.editIndex, self.editEntry)
        if self.tabIndex == 1:
            self.doneList.currentItem().setText(self.editEntry)
            self.undoRedoDone.insert(self.editIndex, self.editEntry)
        self.undoRedoUpdateLists()

    def getEditEntry(self):
        if self.sender().text() == self.okEditButton.text():
            if self.editInput.text() is not "":
                self.addEditEntry()
        elif self.sender().text() == self.cancelEditButton.text():
            self.editInput.setText("")
            self.editItems.hide()


def main():
    app = QtWidgets.QApplication(sys.argv)
    #print(app.desktop().screenGeometry().width(), app.desktop().screenGeometry().height())
    font_db = QtGui.QFontDatabase()
    font_id = font_db.addApplicationFont("Handlee-Regular.ttf")
    handleeFont = QtGui.QFont("Handlee", 25)
    app.setFont(handleeFont)
    w = Window()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
