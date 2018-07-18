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
import subprocess
import cv2
import matplotlib.pyplot as plt
from PIL import Image
import os


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
            self.pen = QtGui.QPen()
            self.pen.setColor(QtGui.QColor(255, 105, 180))
            self.pen.setWidth(10)
            self.qp.setPen(self.pen)
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
    on_item_select_todo = QtCore.pyqtSignal(int, QtWidgets.QListWidgetItem)
    on_item_change_todo = QtCore.pyqtSignal(QtWidgets.QListWidgetItem)
    on_item_select_done = QtCore.pyqtSignal(int, str)
    on_item_change_done = QtCore.pyqtSignal(int, QtWidgets.QListWidgetItem)
    on_done_change = QtCore.pyqtSignal(QtWidgets.QListWidgetItem)
    one_move_up = QtCore.pyqtSignal(int)
    one_move_down = QtCore.pyqtSignal(int)
    on_move_up_all = QtCore.pyqtSignal(int)
    on_move_down_all = QtCore.pyqtSignal(int)
    on_select_up = QtCore.pyqtSignal(int)
    on_select_down = QtCore.pyqtSignal(int)
    on_select_left = QtCore.pyqtSignal(int)
    on_select_right = QtCore.pyqtSignal(int)

    def __init__(self, wm, addr):
        super().__init__()

        self.on_item_select_todo.connect(self.on_item_selection_todoList)
        self.on_item_select_done.connect(self.on_item_select_doneList)
        self.one_move_up.connect(self.moveItemOneUp)
        self.one_move_down.connect(self.moveItemOneDown)
        self.on_move_up_all.connect(self.moveItemToTop)
        self.one_move_down.connect(self.moveItemToBottom)
        self.on_select_up.connect(self.arrowUpReleased)
        self.on_select_down.connect(self.arrowDownReleased)
        self.on_item_change_done.connect(self.change_item_donelist)
        self.on_item_change_todo.connect(self.change_item_todolist)
        self.on_done_change.connect(self.change_donelist)

        self.btaddr = addr
        #self.btaddr = "18:2A:7B:F3:F8:F5"
        #self.btaddr = "B8:AE:6E:1B:AD:A0"
        #self.btaddr = "B8:AE:6E:50:05:32"

        self.mediumvioletred = 'rgb(199,21,133)'

        self.wiimote = wm
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
        self.undoOne = False
        self.redoTwo = False

        self.arrowUp = False
        self.arrowDown = False
        self.leftButton = False
        self.opened = False
        self.rightButton = False
        self.movieOpened = False

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
        self.todoIndex = -1
        self.doneIndex = -1
        self.indicesStatus = []
        self.indices = [[self.todoIndex, self.doneIndex]]

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

        self.layout = QtWidgets.QHBoxLayout()
        layoutSettings = QtWidgets.QVBoxLayout()
        self.layoutList = QtWidgets.QVBoxLayout()

        self.draw_widget = DrawWidget(self)
        self.draw_widget.setParent(self)
        self.draw_widget.setGeometry(self.x(), self.y(), self.width(), self.height())

        # layoutSettings with undo and redo buttons
        self.undoButton = QtWidgets.QPushButton("")
        self.undoButton.clicked.connect(self.undo)
        self.redoButton = QtWidgets.QPushButton("")
        self.redoButton.clicked.connect(self.redo)
        # layoutSettings with add and delete button
        self.deleteButton = QtWidgets.QPushButton("")
        self.newItemButton = QtWidgets.QPushButton("")
        self.deleteButton.clicked.connect(self.delete)
        self.deleteButton.setObjectName("deleteButton")
        self.newItemButton.clicked.connect(self.addnewItem)
        # set an icon to the delete-, add-, undo- and redo-button
        self.deleteButton.setIcon(QtGui.QIcon('delete-button.svg'))
        self.deleteButton.setIconSize(QtCore.QSize(150, 150))
        self.deleteButton.setStyleSheet("background-color: " + self.mediumvioletred)
        self.newItemButton.setIcon(QtGui.QIcon('add-button.svg'))
        self.newItemButton.setIconSize(QtCore.QSize(150, 150))
        self.newItemButton.setStyleSheet("background-color: " + self.mediumvioletred)
        self.redoButton.setIcon(QtGui.QIcon('redo-button.svg'))
        self.redoButton.setIconSize(QtCore.QSize(150, 150))
        self.redoButton.setStyleSheet("background-color: " + self.mediumvioletred)
        self.undoButton.setIcon(QtGui.QIcon('undo-button.svg'))
        self.undoButton.setIconSize(QtCore.QSize(150, 150))
        self.undoButton.setStyleSheet("background-color: " + self.mediumvioletred)
        title = QtWidgets.QLabel("ToDo-List")
        title.setStyleSheet("color: " + self.mediumvioletred + "; font-size: 80px; qproperty-alignment: 'AlignCenter'")
        self.layoutList.addWidget(title)

        layoutSettings.addWidget(self.deleteButton)
        layoutSettings.addWidget(self.newItemButton)
        layoutSettings.addWidget(self.undoButton)

        layoutSettings.addWidget(self.redoButton)
        layoutSettings.setAlignment(QtCore.Qt.AlignBottom)

        # init tabs
        self.tab = QtWidgets.QTabWidget()
        self.tabToDo = QtWidgets.QWidget()
        self.tabDone = QtWidgets.QWidget()
        self.tab.addTab(self.tabToDo, "To Do")
        self.tab.addTab(self.tabDone, "Done")
        self.tab.setStyleSheet("color: " + self.mediumvioletred)
        self.layoutList.addWidget(self.tab)

        # listWidget ToDoList
        # transparent background from source https://stackoverflow.com/questions/27497209/how-to-make-a-qwidget-based-
        # window-have-a-transparent-background
        self.toDoList = QtWidgets.QListWidget()

        p = QtGui.QPalette()
        p.setColor(QtGui.QPalette.Highlight, QtGui.QColor(199, 21, 133))
        self.toDoList.setPalette(p)

        layoutListToDoWidget = QtWidgets.QHBoxLayout()
        layoutListToDoWidget.addWidget(self.toDoList)
        self.tabToDo.setLayout(layoutListToDoWidget)
        self.tabToDo.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.toDoList.setStyleSheet("QListWidget::indicator:unchecked{image: url(unchecked.svg)}")

        # listWidget DoneList
        self.doneList = QtWidgets.QListWidget()
        self.doneList.setStyleSheet("QListWidget::indicator:checked{image: url(checked.svg)}")
        self.doneList.setPalette(p)
        layoutListDoneWidget = QtWidgets.QHBoxLayout()
        layoutListDoneWidget.addWidget(self.doneList)
        self.tabDone.setLayout(layoutListDoneWidget)

        self.toDoList.itemClicked.connect(self.checkItemOnToDoList)
        self.doneList.itemClicked.connect(self.checkItemOnDoneList)

        # init Popup
        self.inputToDo = QtWidgets.QWidget()
        self.inputToDo.setStyleSheet("background-color: white")
        self.inputToDo.setGeometry(0,0, int(self.width()/2), int(self.height()/4))
        layoutPopup = QtWidgets.QVBoxLayout()
        layoutInput = QtWidgets.QVBoxLayout()
        layoutButtons = QtWidgets.QHBoxLayout()
        self.inputToDo.setWindowTitle("New To Do")
        labelInput = QtWidgets.QLabel("Type in new To Do:")
        #labelInput.setStyleSheet("color: " + self.mediumvioletred)
        self.editToDo = QtWidgets.QLineEdit()
        self.editToDo.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.editToDo.setStyleSheet("QLineEdit:focus{border: 1px solid "+ self.mediumvioletred + "}")
        self.okButton = QtWidgets.QPushButton("OK")
        self.okButton.setFixedHeight(80)
        self.okButton.clicked.connect(self.getNewEntry)
        self.okButton.setStyleSheet("background-color: " + self.mediumvioletred + "; border-radius: 2px ; color: white")
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.getNewEntry)
        self.cancelButton.setStyleSheet("color: " + self.mediumvioletred + "; border-radius: 2px ; border: 1px solid " + self.mediumvioletred)
        self.cancelButton.setFixedHeight(80)

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
        self.editItems.setStyleSheet("background-color: white")
        self.editItems.setGeometry(0, 0, int(self.width()/2), int(self.height()/4))
        layoutEditPopup = QtWidgets.QVBoxLayout()
        layoutEditInputPopup = QtWidgets.QVBoxLayout()
        layoutEditButtons = QtWidgets.QHBoxLayout()
        self.editItems.setWindowTitle("Edit Item")
        self.labelEditInput = QtWidgets.QLabel("Edit:")
        self.editInput = QtWidgets.QLineEdit()
        self.editInput.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.editInput.setStyleSheet("QLineEdit:focus{border: 1px solid "+ self.mediumvioletred + "}")
        self.okEditButton = QtWidgets.QPushButton("OK")
        self.okEditButton.clicked.connect(self.getEditEntry)
        self.okEditButton.setStyleSheet("background-color: " + self.mediumvioletred + "; border-radius: 2px ; color: white")
        self.okEditButton.setFixedHeight(80)

        self.cancelEditButton = QtWidgets.QPushButton("Cancel")
        self.cancelEditButton.clicked.connect(self.getEditEntry)
        self.cancelEditButton.setStyleSheet("color: " + self.mediumvioletred + "; border-radius: 2px ; border: 1px solid " + self.mediumvioletred)
        self.cancelEditButton.setFixedHeight(80)

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
        self.layout.addLayout(self.layoutList)
        self.layout.addLayout(layoutSettings)
        self.setLayout(self.layout)
        self.show()

    def change_item_todolist(self, item):
        self.toDoList.setCurrentItem(item)

    def change_donelist(self, item):
        print("doneList", self.doneList.selectedItems())
        self.doneList.setCurrentItem(item)
        print("happy end")

    def change_item_donelist(self, index, item):
        item.setCheckState(QtCore.Qt.Unchecked)
        self.doneList.insertItem(index, item)
        self.doneList.setCurrentItem(item)

    def on_item_selection_todoList(self, index, item):
        item.setCheckState(QtCore.Qt.Unchecked)
        self.toDoList.insertItem(index, item)
        self.toDoList.setCurrentItem(item)

    def on_item_select_doneList(self, index, item):
        newItem = QtWidgets.QListWidgetItem(item)
        newItem.setCheckState(QtCore.Qt.Checked)
        self.doneList.insertItem(index, newItem)
        self.doneList.setCurrentItem(newItem)

    def connect_wiimote(self):
        # self.wiimote = wiimote.connect(self.btaddr)

        if self.wiimote is not None:
            self.wiimote.ir.register_callback(self.process_wiimote_ir_data)
            self.wiimote.buttons.register_callback(self.getPressedButton)
            self.set_update_rate(20)

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

                if x >= xUndo:
                    if x <= xUndo + self.undoButton.width():
                        if y >= yUndo:
                            if y <= yUndo + self.undoButton.height():
                                self.buttonA = False
                                self.undo()

                elif x >= xRedo:
                    if x <= xRedo + self.redoButton.width():
                        if y >= yRedo:
                            if y <= yRedo + self.redoButton.height():
                                self.buttonA = False
                                self.redo()

                elif x >= xDelete:
                    if x <= xDelete + self.deleteButton.width():
                        if y >= yDelete:
                            if y <= yDelete + self.deleteButton.height():
                                self.buttonA = False
                                self.delete()

                elif x >= xaddItem:
                    if x <= xaddItem + self.newItemButton.width():
                        if y >= yaddItem:
                            if y <= yaddItem + self.newItemButton.height():
                                self.buttonA = False
                                self.addnewItem()

                elif self.editItems.isVisible():
                    if x >= xEdit + xItems:
                        if x <= xEdit + self.okEditButton.width() + xItems:
                            if y >= yEdit + yItems:
                                if y <= yEdit + self.okEditButton.height() + yItems:
                                    self.buttonA = False
                                    self.addEditEntry()
                elif self.editItems.isVisible():
                    if x >= xEditCancel + xItems:
                        if x <= xEditCancel + self.cancelEditButton.width() + xItems:
                            if y >= yEditCancel + yItems:
                                if y <= yEditCancel + self.cancelEditButton.height() + yItems:
                                    self.buttonA = False
                                    self.editItems.hide()
                elif self.inputToDo.isVisible():
                    if x >= xAdd + xInput:
                        if x <= xAdd + self.okButton.width() + xInput:
                            if y >= yAdd + yInput:
                                if y <= yAdd + self.okButton.height() + yInput:
                                    self.buttonA = False
                                    if self.editToDo.text() is not "":
                                        self.addNewEntry()
                                        self.editToDo.setText("")
                elif self.inputToDo.isVisible():
                    if x >= xAddCancel + xInput:
                        if x <= xAddCancel + self.cancelButton.width() + xInput:
                            if y >= yAddCancel + yInput:
                                if y <= yAddCancel + self.cancelButton.height() + yInput:
                                    self.buttonA = False
                                    self.inputToDo.hide()
                                    self.editToDo.setText("")

                else:
                    self.buttonA = False
                    if self.predicted == 0:
                        self.delete()


        # if the 'Plus'-Button is released an the wiimote is not moving the current item will be moved up by one element
        if self.wiimote.buttons['Plus'] and self.predicted == 2:
            self.moveOneUp = True
        else:
            self.moveOneUp = False
            self.one_move_up.emit(getCurrentTab)

         # if the 'Minus'-Button is released an the wiimote is not moving the current item will be moved down by one element
        if self.wiimote.buttons['Minus'] and self.predicted == 2:
            self.moveOneDown = True
        else:
            self.moveOneDown = False
            self.one_move_down.emit(getCurrentTab)

        # if the 'Plus'-Button is released an the wiimote is moved slightly up and down the current item will be moved to the bottom of the list
        if self.wiimote.buttons['Plus'] and self.predicted == 1:
            self.moveCompleteUp = True
        else:
            #self.moveCompleteUp = False
            self.on_move_up_all.emit(getCurrentTab)

        # if the 'Minus'-Button is released an the wiimote is moved slightly up and down the current item will be moved to the top of the list
        if self.wiimote.buttons['Minus'] and self.predicted == 1:
            self.moveCompleteDown = True
        else:
            self.moveCompleteDown = False
            self.on_move_down_all.emit(getCurrentTab)

        # if the 'Up'-Button is released the higher Item will be selected
        if self.wiimote.buttons['Up']:
            self.arrowUp = True
        else:
            self.arrowUpReleased(getCurrentTab)
        # if the 'Down'-Button is released the lower Item will be selected
        if self.wiimote.buttons['Down']:
            self.arrowDown = True
        else:
            self.arrowDownReleased(getCurrentTab)

        if self.wiimote.buttons['Left']:
            self.leftButton = True
        else:
            if self.tab.currentIndex() is not 0:
                if self.leftButton is True:
                    self.tab.setCurrentIndex(0)
                    self.leftButton = False
        if self.wiimote.buttons['Right']:
            self.rightButton = True
        else:
            if self.tab.currentIndex() is not 1:
                if self.rightButton is True:
                    self.tab.setCurrentIndex(1)
                    self.rightButton = False

        if self.wiimote.buttons['One']:
            self.undoOne = True
        else:
            if self.undoOne:
                self.undoOne = False
                self.undo()

        if self.wiimote.buttons['Two']:
            self.redoTwo = True
        else:
            if self.redoTwo:
                self.redoTwo = False
                self.redo()

        self.update()

    # the selected item will be positioned one item higher (for do and done list)
    def moveItemOneUp(self, getCurrentTab):
        itemTodo = self.toDoList.currentRow()
        itemDone = self.doneList.currentRow()
        self.todoIndex = itemTodo
        self.doneIndex = itemDone
        #self.undoRedoIndicesUpdate(1)

        if itemTodo is not None and itemTodo >= 0 and self.moveOneUp is True and getCurrentTab == 0:
            self.moveOneUp = False

            currentItem = self.toDoList.takeItem(itemTodo)

            del self.undoRedoTodo[itemTodo]
            self.undoRedoTodo.insert(itemTodo - 1, currentItem.text())
            self.todoIndex = itemTodo - 1
            self.undoRedoUpdateLists()
            #self.toDoList.insertItem(itemTodo - 1, currentItem)
            #self.toDoList.setCurrentItem(currentItem)
            self.on_item_select_todo.emit(itemTodo - 1, currentItem)

        elif itemDone is not None and itemDone >= 0 and self.moveOneUp is True and getCurrentTab == 1:
            self.moveOneUp = False
            currentItem = self.doneList.takeItem(itemDone)
            del self.undoRedoDone[itemDone]
            self.undoRedoDone.insert(itemDone - 1, currentItem.text())
            self.doneIndex = itemDone - 1
            self.undoRedoUpdateLists()
            #self.doneList.insertItem(itemDone - 1, currentItem)
            #self.doneList.setCurrentItem(currentItem)
            self.on_item_change_done.emit(itemDone - 1 , currentItem)

    # the selected item will be positioned one item lower (for do and done list)
    def moveItemOneDown(self, getCurrentTab):
            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()
            self.todoIndex = itemToDo
            self.doneIndex = itemDone
            #self.undoRedoIndicesUpdate(1)

            if itemToDo is not None and itemToDo >= 0 and self.moveOneDown is True and getCurrentTab == 0:
                self.moveOneDown = False

                currentItem = self.toDoList.takeItem(itemToDo)
                del self.undoRedoTodo[itemToDo]
                self.undoRedoTodo.insert(itemToDo + 1, currentItem.text())
                self.todoIndex = itemToDo + 1
                self.undoRedoUpdateLists()
                #self.toDoList.insertItem(itemToDo + 1, currentItem)
                #self.toDoList.setCurrentItem(currentItem)
                self.on_item_select_todo.emit(itemToDo + 1, currentItem)

            elif itemDone is not None and itemDone >= 0 and self.moveOneDown is True and getCurrentTab == 1:
                self.moveOneDown = False
                currentItem = self.doneList.takeItem(itemDone)
                del self.undoRedoDone[itemDone]
                self.undoRedoDone.insert(itemDone + 1, currentItem.text())
                self.doneIndex = itemDone + 1
                self.undoRedoUpdateLists()
                #self.doneList.insertItem(itemDone + 1, currentItem)
                #self.doneList.setCurrentItem(currentItem)
                self.on_item_change_done.emit(itemToDo + 1, currentItem)

    # the selected item will be positioned on the top of the list (for do and done list)
    def moveItemToTop(self, getCurrentTab):
        itemToDo = self.toDoList.currentRow()
        itemDone = self.doneList.currentRow()
        self.todoIndex = itemToDo
        self.doneIndex = itemDone
        #self.undoRedoIndicesUpdate(1)

        if itemToDo is not None and itemToDo >= 0 and self.moveCompleteUp is True and getCurrentTab == 0:
            self.moveCompleteUp = False

            currentItem = self.toDoList.takeItem(itemToDo)
            del self.undoRedoTodo[itemToDo]
            self.undoRedoTodo.insert(0, currentItem.text())
            self.todoIndex = 0
            self.undoRedoUpdateLists()

            #self.toDoList.insertItem(0, currentItem)
            #self.toDoList.setCurrentItem(currentItem)
            self.on_item_select_todo.emit(0, currentItem)

        elif itemDone is not None and itemDone >= 0 and self.moveCompleteUp is True and getCurrentTab == 1:
            self.moveCompleteUp = False

            currentItem = self.doneList.takeItem(itemDone)
            del self.undoRedoDone[itemDone]
            self.undoRedoDone.insert(0, currentItem.text())
            self.doneIndex = 0
            self.undoRedoUpdateLists()

            #self.doneList.insertItem(0, currentItem)
            #self.doneList.setCurrentItem(currentItem)
            self.on_item_change_done.emit(0, currentItem)

    # the selected item will be positioned on the bottom of the list (for do and done list)
    def moveItemToBottom(self, getCurrentTab):

            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()
            self.todoIndex = itemToDo
            self.doneIndex = itemDone
            #self.undoRedoIndicesUpdate(1)

            if itemToDo is not None:
                if itemToDo >= 0:
                    if self.moveCompleteDown is True:
                        if getCurrentTab == 0:
                            self.moveCompleteDown = False
                            newitempos = len(self.toDoList)
                            currentItem = self.toDoList.takeItem(itemToDo)
                            del self.undoRedoTodo[itemToDo]
                            self.undoRedoTodo.insert(newitempos, currentItem.text())
                            self.todoIndex = newitempos
                            self.undoRedoUpdateLists()

                            #self.toDoList.insertItem(newitempos, currentItem)
                            #self.toDoList.setCurrentItem(currentItem)
                            self.on_item_select_todo.emit(newitempos, currentItem)

            elif itemDone is not None:
                if itemDone >= 0:
                    if self.moveCompleteDown is True:
                        if getCurrentTab == 1:
                            self.moveCompleteDown = False
                            newitempos = len(self.doneList)
                            currentItem = self.doneList.takeItem(itemDone)
                            del self.undoRedoDone[itemDone]
                            self.undoRedoDone.insert(newitempos, currentItem.text())
                            self.doneIndex = newitempos
                            self.undoRedoUpdateLists()
                            #self.doneList.insertItem(newitempos, currentItem)
                            #self.doneList.setCurrentItem(currentItem)
                            self.on_item_change_done.emit(newitempos, currentItem)

    # the next higher element in the list will be selected (for do and done list)
    def arrowUpReleased(self, getCurrentTab):
            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None:
                if itemToDo >= 0:
                    if self.arrowUp is True:
                        if getCurrentTab == 0:
                            self.arrowUp = False
                            currentRow = self.toDoList.currentRow()
                            newRow = currentRow -1
                            if currentRow > 0:
                                self.toDoList.setCurrentRow(newRow)

            elif itemDone is not None:
                if itemDone >= 0:
                    if self.arrowUp is True:
                        if getCurrentTab == 1:
                            self.arrowUp = False
                            newitempos = len(self.doneList)
                            currentRow = self.doneList.currentRow()
                            newRow = currentRow -1

                            itemToSelect = self.doneList.item(newRow)
                            if currentRow > 0:
                                self.doneList.setCurrentRow(newRow)

    # the next lower element in the list will be selected (for do and done list)
    def arrowDownReleased(self, getCurrentTab):
            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None:
                if itemToDo >= 0:
                    if self.arrowDown is True:
                        if getCurrentTab == 0:
                            self.arrowDown = False
                            newitempos = len(self.toDoList)
                            currentRow = self.toDoList.currentRow()
                            newRow = currentRow +1
                            if currentRow < newitempos -1:
                                self.toDoList.setCurrentRow(newRow)

            elif itemDone is not None:
                if itemDone >= 0:
                    if self.arrowDown is True:
                        if getCurrentTab == 1:
                            self.arrowDown = False
                            newitempos = len(self.doneList)
                            currentRow = self.doneList.currentRow()
                            newRow = currentRow +1
                            if currentRow < newitempos -1:
                                self.doneList.setCurrentRow(newRow)

    # https://stackoverflow.com/questions/33953776/how-to-open-and-close-a-website-using-default-browser-with-python
    # last access: 13.07.2018
    # if left Button ist Pressed without moving the wiimote a website will be opened
    # if left Button is Pressed while shaking the wiimote from the left to the right side the website will be closed
    def leftButtonPressed(self):
        if self.predicted == 2 and self.opened is False and self.leftButton is True:
            print("Website öffnen")
            try:
                self.website = subprocess.Popen(["firefox", "http://www.kamelrechner.eu/de"])
            except:
                print("Fehler beim öffnen der Website")
            self.opened = False
        #elif self.predicted == 0 and self.opened is True and self.leftButton is False:
         #   print("website schließen")
         #   self.opened = False
          #  try:
          #      self.website.kill()
           # except:
            #    print("Fehler beim schließen der Website")

    # a video will be shown
    def rightButtonPressed(self):

        if self.predicted == 2 and self.movieOpened is False and self.rightButton is True:
            filename = "katze.png"
            self.image = Image.open(filename).show()

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
            self.todoIndex = item
            self.doneIndex = self.doneList.currentRow()
            #self.undoRedoIndicesUpdate(1)
            if item is not -1:
                del self.undoRedoTodo[item]
                self.todoIndex = 0
                self.undoRedoUpdateLists()
                self.toDoList.takeItem(item)
                itemToSelect = self.toDoList.item(0)
                if itemToSelect is not None:
                    self.on_item_select_todo.emit(0, itemToSelect)
        if getCurrentTab == 1:
            item = self.doneList.currentRow()
            self.doneIndex = item
            self.todoIndex = self.toDoList.currentRow()
            #self.undoRedoIndicesUpdate(1)
            del self.undoRedoDone[item]
            self.doneIndex = 0
            self.undoRedoUpdateLists()
            self.doneList.takeItem(item)
            itemToSelect = self.doneList.item(0)
            if itemToSelect is not None:
                self.doneList.setCurrentItem(itemToSelect)

    def addnewItem(self):
        self.editToDo.setFocus()
        self.inputToDo.show()

    # sets the to do list to a new state
    def undoRedoTodoList(self):
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoTodo = self.undoRedo[self.undoRedoIndex][0][:]
        self.toDoList.clear()
        if len(self.undoRedoTodo) > 0:
            for i in range(len(self.undoRedoTodo)):
                if len(self.undoRedoTodo) is not 0:
                    item = QtWidgets.QListWidgetItem(self.undoRedoTodo[i])
                    item.setCheckState(QtCore.Qt.Unchecked)
                    self.toDoList.addItem(item)
                if i == 0:
                    firstItem = item
            self.on_item_select_todo.emit(0, firstItem)
        #print("len", len(self.undoRedo), len(self.indices), self.undoRedoIndex)
       # if len(self.toDoList) > 0:
        #    print("todo", firstItem.text())
         #   self.toDoList.setCurrentItem(firstItem)
        #self.toDoList.show()
        #if len(self.indices) + self.undoRedoIndex >= 0:
            #print("here")
         #   if self.indices[self.undoRedoIndex][0] > -1:
                #print("there", self.indices, self.indices[self.undoRedoIndex][0])
                # self.toDoList.setCurrentRow(self.indices[self.undoRedoIndex][0])
        #self.on_item_select_todo.emit(0, item)

    # sets the done list to a new state
    def undoRedoDoneList(self):
        firstItem = ""
        if len(self.undoRedo) + self.undoRedoIndex >= 0:
            self.undoRedoDone = self.undoRedo[self.undoRedoIndex][1][:]
        self.doneList.clear()
        if len(self.undoRedoDone) > 0:
            for i in range(len(self.undoRedoDone)):
                if len(self.undoRedoDone) is not 0:
                    item = QtWidgets.QListWidgetItem(self.undoRedoDone[i])
                    item.setCheckState(QtCore.Qt.Checked)
                    self.doneList.addItem(item)
                if i == 0:
                    firstItem = item.text()

            self.on_item_select_done.emit(0, firstItem)
        #self.doneList.show()
        #if len(self.doneList) > 0:
         #   print("done")
          #  self.doneList.setCurrentItem(self.doneList[0])
        #if len(self.indices) + self.undoRedoIndex >= 0:
         #   if self.indices[self.undoRedoIndex][0] > -1:
                # self.doneList.setCurrentRow(self.indices[self.undoRedoIndex][0])
        #self.on_item_select_done.emit(0, item)

    # if a action like add, remove, check, uncheck was made, the tod o and undo lists are updated
    def undoRedoUpdateLists(self):
        self.current = []
        self.indicesStatus = []
        self.current.append(self.undoRedoTodo[:])
        self.current.append(self.undoRedoDone[:])
        if self.status == "undo":
            self.undoRedo = self.undoRedo[:(self.undoRedoIndex + 1)][:]
            self.indices = self.indices[:(self.undoRedoIndex + 1)][:]
            self.undoRedoIndex = -1
            self.status = ""
        #self.undoRedoIndicesUpdate(0)
        self.undoRedo.append(self.current[:])
        if len(self.undoRedo) > self.undoRedoLength:
            length = len(self.undoRedo) - self.undoRedoLength
            self.undoRedo = self.undoRedo[length:][:]
            self.indices = self.indices[length:][:]

    def undoRedoIndicesUpdate(self, status):
        if len(self.toDoList) == 0:
            self.todoIndex = -1
        if len(self.doneList) == 0:
            self.doneIndex = -1
        if status == 1:
            #print(self.indices[-1])
            del self.indices[-1]
        self.indicesStatus.append(self.todoIndex)
        self.indicesStatus.append(self.doneIndex)
        self.indices.append(self.indicesStatus[:])
        self.indicesStatus = []

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
            self.raiseWidgets()
            self.draw_widget.raise_()
            self.draw_widget.setFocusPolicy(QtCore.Qt.StrongFocus)

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

        #if event.type() == QtCore.QEvent.MouseButtonPress and widget is self.toDoList:

        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def recognizeDrawing(self, pos):
        self.pos = pos
        if len(self.pos) > 0:
            recognized = self.recognizer.recognizeGesture(self.pos)
            self.recognizedAction(recognized)

    # source: jupyter notebook "Signals, Noise, Filters", ITT
    #def moving_average(self, pos):
     #   filtered_signal = []
      #  width = 10
       # for i in range(len(pos)):
        #    filtered_signal.append(sum(pos[i][i-width:i]/width))
        #return filtered_signal

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
                self.todoIndex = self.toDoList.currentRow()
                self.doneIndex = self.doneList.currentRow()
                #self.undoRedoIndicesUpdate(1)
                item = self.toDoList.currentItem()
                text = item.text()
                self.undoRedoDone.append(text)
                del self.undoRedoTodo[self.toDoList.row(item)]
                self.toDoList.takeItem(self.toDoList.row(item))
                self.todoIndex = 0
                self.doneIndex = 0
                self.undoRedoUpdateLists()
                #newItem = QtWidgets.QListWidgetItem(text)
                #newItem.setCheckState(QtCore.Qt.Checked)
                #self.doneList.insertItem(0, newItem)
                #self.doneList.setCurrentItem(newItem)
                self.on_item_select_done.emit(0, text)
                if len(self.toDoList) > 0:
                    item = self.toDoList.item(0)
                    self.on_item_change_todo.emit(item)
        elif recognized == "Uncheck":
            if self.doneList.currentItem() is not None:
                self.doneIndex = self.doneList.currentRow()
                self.todoIndex = self.toDoList.currentRow()
                #self.undoRedoIndicesUpdate(1)
                item = self.doneList.currentItem()
                self.undoRedoTodo.append(item.text())
                del self.undoRedoDone[self.toDoList.row(item)]
                self.doneList.takeItem(self.doneList.row(item))
                newItem = QtWidgets.QListWidgetItem(item.text())
                print("uncheck", newItem)
                self.on_item_select_todo.emit(0, newItem)
                #newItem.setCheckState(QtCore.Qt.Unchecked)
                #self.toDoList.insertItem(0, newItem)
                #self.toDoList.setCurrentItem(newItem)
                print("uncheck: select to do")
                self.todoIndex = 0
                self.doneIndex = 0
                self.undoRedoUpdateLists()

                if len(self.doneList) > 0:
                    item = self.doneList.item(0)
                    print("uncheck: donelist signal", item.text())
                    self.on_done_change.emit(item)

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
        else:
            pass

    def checkItemOnToDoList(self, item):
        if item.checkState() == QtCore.Qt.Checked:
            self.toDoList.takeItem(self.toDoList.row(item))
            text = item.text()
            #newItem = QtWidgets.QListWidgetItem(item.text())
            #newItem.setCheckState(QtCore.Qt.Checked)
            #self.doneList.insertItem(0, newItem)
            self.on_item_select_done.emit(0, text)


    def checkItemOnDoneList(self, item):
        if item.checkState() == QtCore.Qt.Unchecked:
            self.doneList.takeItem(self.doneList.row(item))
            newItem = QtWidgets.QListWidgetItem(item.text())
            #newItem.setCheckState(QtCore.Qt.Unchecked)
            #self.toDoList.insertItem(0, newItem)
            self.on_item_select_todo.emit(0, newItem)

    def addNewEntry(self):
        self.newEntry = self.editToDo.text()
        self.undoRedoTodo.insert(0, self.newEntry)
        self.todoIndex = 0
        if self.status == "undo":
            self.undoRedo = self.undoRedo[:self.undoRedoIndex + 1][:]
            self.undoRedoIndex = -1
            self.status = ""
        self.editToDo.setText("")
        self.inputToDo.hide()
        item = QtWidgets.QListWidgetItem(self.newEntry)
        #item.setCheckState(QtCore.Qt.Unchecked)
        #self.toDoList.insertItem(0, item)
        #self.toDoList.setCurrentItem(item)
        self.on_item_select_todo.emit(0, item)
        self.undoRedoUpdateLists()
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
            self.todoIndex = self.editIndex
        if self.tabIndex == 1:
            self.doneList.currentItem().setText(self.editEntry)
            self.undoRedoDone.insert(self.editIndex, self.editEntry)
            self.doneIndex = self.editIndex
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
    handleeFont = QtGui.QFont("Handlee", 50)
    app.setFont(handleeFont)
    wiimote_connection()

    sys.exit(app.exec_())

def wiimote_connection():
    try:
        #self.connect_wiimote()
        input("Press the 'sync' button on the back of your Wiimote Plus or "
              "enter the the MAC adress of your Wiimote \n" +
              "Press <return> once the Wiimote's LEDs start blinking. \n")

        if len(sys.argv) == 1:
            addr, name = wiimote.find()[0]
        elif len(sys.argv) == 2:
            addr = sys.argv[1]
            name = None
        elif len(sys.argv) == 3:
            addr, name = sys.argv[1:3]
        print(("Connecting to %s (%s)" % (name, addr)))
        wm = wiimote.connect(addr, name)
        w = Window(wm, addr)

    except Exception as e:
        print(e, ", no wiimote found")


if __name__ == '__main__':
    main()
