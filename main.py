#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

import wiimote
from recognizer import Recognizer
from transform import Transform
from PyQt5 import QtWidgets, QtCore, QtGui
from pylab import *
from sklearn import svm
from draw import DrawWidget
import numpy as np
import sys
import training_activity
import fft_svm
import undo_redo
import webbrowser


class Window(QtWidgets.QWidget):

    def __init__(self, wm, app):
        super().__init__()

        self.mvr = 'rgb(199,21,133)'

        self.wiimote = wm
        self.app = app
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
        self.home = False

        self.arrowUp = False
        self.arrowDown = False
        self.leftButton = False
        self.opened = False
        self.rightButton = False
        self.movieOpened = False

        self.transform_x = []
        self.transform_y = []

        self.featureVector = training_activity.TrainingData.featureVector
        self.trainingDataTest = training_activity.TrainingData.trainingDataTest

        self.trainingData = []
        self.trainingData.append(self.trainingDataTest)
        self.c = svm.SVC()
        self.fourier = []
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_all_sensors)

        self.pos = []
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.recognizer = Recognizer()
        self.transform = Transform()
        self.undoRedo = undo_redo.UndoRedo()
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

        self.setGeometry(0, 0, 1920, 950)
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
        self.deleteButton.setStyleSheet("background-color: " + self.mvr)
        self.newItemButton.setIcon(QtGui.QIcon('add-button.svg'))
        self.newItemButton.setIconSize(QtCore.QSize(150, 150))
        self.newItemButton.setStyleSheet("background-color: " + self.mvr)
        self.redoButton.setIcon(QtGui.QIcon('redo-button.svg'))
        self.redoButton.setIconSize(QtCore.QSize(150, 150))
        self.redoButton.setStyleSheet("background-color: " + self.mvr)
        self.undoButton.setIcon(QtGui.QIcon('undo-button.svg'))
        self.undoButton.setIconSize(QtCore.QSize(150, 150))
        self.undoButton.setStyleSheet("background-color: " + self.mvr)
        title = QtWidgets.QLabel("ToDo-List")
        title.setStyleSheet("color: " + self.mvr + "; font-size: 80px; qproperty-alignment: 'AlignCenter'")
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
        self.tab.setStyleSheet("color: " + self.mvr)
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
        self.inputToDo.setGeometry(0, 0, int(self.width()/2), int(self.height()/4))
        layoutPopup = QtWidgets.QVBoxLayout()
        layoutInput = QtWidgets.QVBoxLayout()
        layoutButtons = QtWidgets.QHBoxLayout()
        self.inputToDo.setWindowTitle("New To Do")
        labelInput = QtWidgets.QLabel("Type in new To Do:")
        self.editToDo = QtWidgets.QLineEdit()
        self.editToDo.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.editToDo.setStyleSheet("QLineEdit:focus{border: 1px solid " + self.mvr + "}")
        self.okButton = QtWidgets.QPushButton("OK")
        self.okButton.setFixedHeight(80)
        self.okButton.clicked.connect(self.getNewEntry)
        self.okButton.setStyleSheet("background-color: " + self.mvr + "; border-radius: 2px ; color: white")
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.getNewEntry)
        self.cancelButton.setStyleSheet("color: " + self.mvr + "; border-radius: 2px ; border: 1px solid " + self.mvr)
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

        # init edit popup window
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
        self.editInput.setStyleSheet("QLineEdit:focus{border: 1px solid " + self.mvr + "}")
        self.okEditButton = QtWidgets.QPushButton("OK")
        self.okEditButton.clicked.connect(self.getEditEntry)
        self.okEditButton.setStyleSheet("background-color: " + self.mvr + "; border-radius: 2px ; color: white")
        self.okEditButton.setFixedHeight(80)
        self.cancelEditButton = QtWidgets.QPushButton("Cancel")
        self.cancelEditButton.clicked.connect(self.getEditEntry)
        self.cancelEditButton.setStyleSheet("color: " + self.mvr + "; border-radius: 2px; border: 1px solid" + self.mvr)
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

    # gets the current undo lists for to do and done and gives them to methods for setting the updated qlistqidgets
    def undo(self):
        undoTodoList, undoDoneList = self.undoRedo.undo()
        self.undoRedoTodo(undoTodoList)
        self.undoRedoDone(undoDoneList)

    # gets the current undo lists for to do and done and gives them to methods for setting the updated qlistwidget
    def redo(self):
        redoTodoList, redoDoneList = self.undoRedo.redo()
        self.undoRedoTodo(redoTodoList)
        self.undoRedoDone(redoDoneList)

    # clears the actual to do list widget and creates a new updated one
    def undoRedoTodo(self, undoRedoTodoList):
        self.toDoList.clear()
        if len(undoRedoTodoList) > 0:
            for i in range(len(undoRedoTodoList)):
                    item = QtWidgets.QListWidgetItem(undoRedoTodoList[i])
                    item.setCheckState(QtCore.Qt.Unchecked)
                    self.toDoList.addItem(item)
        if self.toDoList.count() > 0:
            self.toDoList.setCurrentRow(0)

    # clears the actual done list widget and creates a new updated one
    def undoRedoDone(self, undoRedoDoneList):
        self.doneList.clear()
        if len(undoRedoDoneList) > 0:
            for i in range(len(undoRedoDoneList)):
                item = QtWidgets.QListWidgetItem(undoRedoDoneList[i])
                item.setCheckState(QtCore.Qt.Checked)
                self.doneList.addItem(item)
            self.doneList.setCurrentRow(0)

    # sets the callbacks for the connected wiimote
    def connect_wiimote(self):
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
            self.app.postEvent(self.toDoList, QtGui.QMouseEvent(QtGui.QMouseEvent.MouseButtonPress, QtCore.QPoint(x, y), QtCore.Qt.LeftButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier))
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
                self.buttonA = False

                self.app.postEvent(self.toDoList, QtGui.QMouseEvent(QtGui.QMouseEvent.MouseButtonRelease, QtCore.QPoint(x, y), QtCore.Qt.LeftButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier))

                if x >= xUndo:
                    if x <= xUndo + self.undoButton.width():
                        if y >= yUndo:
                            if y <= yUndo + self.undoButton.height():
                                self.buttonA = False
                                self.undo()

                if x >= xRedo:
                    if x <= xRedo + self.redoButton.width():
                        if y >= yRedo:
                            if y <= yRedo + self.redoButton.height():
                                self.buttonA = False
                                self.redo()

                if x >= xDelete:
                    if x <= xDelete + self.deleteButton.width():
                        if y >= yDelete:
                            if y <= yDelete + self.deleteButton.height():
                                self.buttonA = False
                                self.delete()

                if x >= xaddItem:
                    if x <= xaddItem + self.newItemButton.width():
                        if y >= yaddItem:
                            if y <= yaddItem + self.newItemButton.height():
                                self.buttonA = False
                                self.addnewItem()

                if self.editItems.isVisible():
                    if x >= xEdit + xItems:
                        if x <= xEdit + self.okEditButton.width() + xItems:
                            if y >= yEdit + yItems:
                                if y <= yEdit + self.okEditButton.height() + yItems:
                                    self.buttonA = False
                                    self.addEditEntry()

                if self.editItems.isVisible():
                    if x >= xEditCancel + xItems:
                        if x <= xEditCancel + self.cancelEditButton.width() + xItems:
                            if y >= yEditCancel + yItems:
                                if y <= yEditCancel + self.cancelEditButton.height() + yItems:
                                    self.buttonA = False
                                    self.editItems.hide()

                if self.inputToDo.isVisible():
                    if x >= xAdd + xInput:
                        if x <= xAdd + self.okButton.width() + xInput:
                            if y >= yAdd + yInput:
                                if y <= yAdd + self.okButton.height() + yInput:
                                    self.buttonA = False
                                    if self.editToDo.text() is not "":
                                        self.addNewEntry()
                                        self.editToDo.setText("")

                if self.inputToDo.isVisible():
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

        self.app.processEvents()

        # if the 'Plus'-Button is released an the wiimote is not moving the current item will be moved up by one element
        if self.wiimote.buttons['Plus'] and self.predicted == 2:
            self.moveOneUp = True
        else:
            self.moveItemOneUp(getCurrentTab)

        # if the 'Minus'-Button is released an the wiimote is not moving
        # the current item will be moved down by one element
        if self.wiimote.buttons['Minus'] and self.predicted == 2:
            self.moveOneDown = True
        else:
            self.moveItemOneDown(getCurrentTab)

        # if the 'Plus'-Button is released an the wiimote is moved slightly up and
        # down the current item will be moved to the bottom of the list
        if self.wiimote.buttons['Plus'] and self.predicted == 1:
            self.moveCompleteUp = True
        else:
            self.moveItemToTop(getCurrentTab)

        # if the 'Minus'-Button is released an the wiimote is moved slightly up and
        # down the current item will be moved to the top of the list
        if self.wiimote.buttons['Minus'] and self.predicted == 1:
            self.moveCompleteDown = True
        else:
            self.moveItemToBottom(getCurrentTab)

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

        if self.wiimote.buttons['Home']:
            self.home = True
        else:
            if self.home is True:
                webbrowser.open("https://www.youtube.com/watch?v=Z2XmDshWkgg")
                self.home = False

        self.update()

    # the selected item will be positioned one item higher (for do and done list)
    def moveItemOneUp(self, getCurrentTab):
        itemTodo = self.toDoList.currentRow()
        itemDone = self.doneList.currentRow()

        if itemTodo is not None:
            if itemTodo > 0:
                if self.moveOneUp is True:
                    if getCurrentTab == 0:
                        self.moveOneUp = False
                        currentItem = self.toDoList.takeItem(itemTodo)
                        self.undoRedo.updateListsOneItemUpTodo(itemTodo, currentItem)
                        self.toDoList.insertItem(itemTodo - 1, currentItem)
                        self.toDoList.setCurrentRow(itemTodo - 1)

        if itemDone is not None:
            if itemDone > 0:
                if self.moveOneUp is True:
                    if getCurrentTab == 1:
                        self.moveOneUp = False
                        currentItem = self.doneList.takeItem(itemDone)
                        self.undoRedo.updateListsOneItemUpDone(itemDone, currentItem)
                        self.doneList.insertItem(itemDone - 1, currentItem)
                        self.doneList.setCurrentRow(itemDone - 1)

    # the selected item will be positioned one item lower (for do and done list)
    def moveItemOneDown(self, getCurrentTab):
            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None:
                if itemToDo < self.toDoList.count():
                    if self.moveOneDown is True:
                        if getCurrentTab == 0:
                            self.moveOneDown = False
                            currentItem = self.toDoList.takeItem(itemToDo)
                            self.undoRedo.updateListsOneItemDownTodo(itemToDo, currentItem)
                            self.toDoList.insertItem(itemToDo + 1, currentItem)
                            self.toDoList.setCurrentRow(itemToDo + 1)

            if itemDone is not None:
                if itemDone < self.doneList.count():
                    if self.moveOneDown is True:
                        if getCurrentTab == 1:
                            self.moveOneDown = False
                            currentItem = self.doneList.takeItem(itemDone)
                            self.undoRedo.updateListsOneItemDownDone(itemDone, currentItem)
                            self.doneList.insertItem(itemDone + 1, currentItem)
                            self.doneList.setCurrentRow(itemDone + 1)

    # the selected item will be positioned on the top of the list (for do and done list)
    def moveItemToTop(self, getCurrentTab):
        itemToDo = self.toDoList.currentRow()
        itemDone = self.doneList.currentRow()

        if itemToDo is not None:
            if itemToDo > 0:
                if self.moveCompleteUp is True:
                    if getCurrentTab == 0:
                        self.moveCompleteUp = False
                        currentItem = self.toDoList.takeItem(itemToDo)
                        self.undoRedo.updateListsItemToTopTodo(itemToDo, currentItem)
                        self.toDoList.insertItem(0, currentItem)
                        self.toDoList.setCurrentRow(0)

        if itemDone is not None:
            if itemDone > 0:
                if self.moveCompleteUp is True:
                    if getCurrentTab == 1:
                        self.moveCompleteUp = False
                        currentItem = self.doneList.takeItem(itemDone)
                        self.undoRedo.updateListsItemToTopDone(itemDone, currentItem)
                        self.doneList.insertItem(0, currentItem)
                        self.doneList.setCurrentRow(0)

    # the selected item will be positioned on the bottom of the list (for do and done list)
    def moveItemToBottom(self, getCurrentTab):

            itemToDo = self.toDoList.currentRow()
            itemDone = self.doneList.currentRow()

            if itemToDo is not None:
                if itemToDo < self.toDoList.count():
                    if self.moveCompleteDown is True:
                        if getCurrentTab == 0:
                            self.moveCompleteDown = False
                            newitempos = self.toDoList.count()
                            currentItem = self.toDoList.takeItem(itemToDo)
                            self.undoRedo.updateListsItemToBottomTodo(itemToDo, currentItem, newitempos)
                            self.toDoList.insertItem(newitempos, currentItem)
                            self.toDoList.setCurrentRow(newitempos)

            if itemDone is not None:
                if itemDone < self.doneList.count():
                    if self.moveCompleteDown is True:
                        if getCurrentTab == 1:
                            self.moveCompleteDown = False
                            newitempos = self.doneList.count()
                            currentItem = self.doneList.takeItem(itemDone)
                            self.undoRedo.updateListsItemToBottomDone(itemToDo, currentItem, newitempos)
                            self.doneList.insertItem(newitempos, currentItem)
                            self.doneList.setCurrentRow(newitempos)

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
                            newRow = currentRow - 1
                            if currentRow > 0:
                                self.toDoList.setCurrentRow(newRow)

            if itemDone is not None:
                if itemDone >= 0:
                    if self.arrowUp is True:
                        if getCurrentTab == 1:
                            self.arrowUp = False
                            currentRow = self.doneList.currentRow()
                            newRow = currentRow - 1

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
                            newitempos = self.toDoList.count()
                            currentRow = self.toDoList.currentRow()
                            newRow = currentRow + 1
                            if currentRow < newitempos - 1:
                                self.toDoList.setCurrentRow(newRow)

            if itemDone is not None:
                if itemDone >= 0:
                    if self.arrowDown is True:
                        if getCurrentTab == 1:
                            self.arrowDown = False
                            newitempos = self.doneList.count()
                            currentRow = self.doneList.currentRow()
                            newRow = currentRow + 1
                            if currentRow < newitempos - 1:
                                self.doneList.setCurrentRow(newRow)

    def delete(self):
        getCurrentTab = self.tab.currentIndex()
        if getCurrentTab == 0:
            item = self.toDoList.currentRow()
            if item is not -1:
                self.toDoList.takeItem(item)
                if self.toDoList.count() > 0:
                    self.toDoList.setCurrentRow(0)
            self.undoRedo.updateListsDelete(getCurrentTab, item)
        if getCurrentTab == 1:
            item = self.doneList.currentRow()
            if item is not -1:
                self.doneList.takeItem(item)
                if self.doneList.count() > 0:
                    self.doneList.setCurrentRow(0)
            self.undoRedo.updateListsDelete(getCurrentTab, item)

    # the popup window for adding a new item is shown
    def addnewItem(self):
        self.editToDo.setFocus()
        self.inputToDo.show()

    def set_update_rate(self, rate):
        if rate == 0:
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
        fftData = fft_svm.ActivityRecognzer.fft(self, x, y, z)
        self.fourier.append(fftData)
        if len(self.fourier) >= 32:
            fft_svm.ActivityRecognzer.svm(self, fftData)
            self.update()

    def update_accel(self, acc_vals):
        self._acc_vals = acc_vals

    def process_wiimote_ir_data(self, event):
        transform_width = 10
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

                self.transform_x.append(x)
                self.transform_y.append(y)
                if len(self.transform_x) > 10:
                    self.transform_x.pop(0)

                if len(self.transform_y) > 10:
                    self.transform_y.pop(0)

                if len(self.transform_x) == transform_width:
                    x = sum(self.transform_x)/len(self.transform_x)

                if len(self.transform_y) == transform_width:
                    y = sum(self.transform_y)/len(self.transform_y)
            except Exception as e:
                print(e)
                x = y = -1

            self.cursor().setPos(self.mapToGlobal(QtCore.QPoint(x, y)))

    # when no wiimote is defined on the widget only can be drawn if "b" is pressed before
    def keyPressEvent(self, event):
        if event.text() == "b":
            self.raiseWidgets()
            self.draw_widget.raise_()
            self.draw_widget.setFocusPolicy(QtCore.Qt.StrongFocus)

    # eventfilter for the key "Return" is installed on the popup windows
    def eventFilter(self, widget, event):
        # source from https://stackoverflow.com/questions/20420072/use-keypressevent-to-catch-enter-or-return
        if event.type() == QtCore.QEvent.KeyPress:
            if widget is self.inputToDo:
                if event.key() == QtCore.Qt.Key_Return:
                    if self.editToDo.text() is not "":
                        self.addNewEntry()
                        return True

        if event.type() == QtCore.QEvent.KeyPress:
            if widget is self.editItems:
                if event.key() == QtCore.Qt.Key_Return:
                    if self.editInput.text() is not "":
                        self.addEditEntry()
                        return True

        return QtWidgets.QWidget.eventFilter(self, widget, event)

    # after a gesture is drawn the points are given to the recognizer
    def recognizeDrawing(self, pos):
        self.pos = pos
        if len(self.pos) > 0:
            recognized = self.recognizer.recognizeGesture(self.pos)
            self.recognizedAction(recognized)

    # after drawing all other widgets are set in front of the window
    def raiseWidgets(self):
        self.undoButton.raise_()
        self.redoButton.raise_()
        self.deleteButton.raise_()
        self.newItemButton.raise_()
        self.tab.raise_()
        self.tabToDo.raise_()
        self.toDoList.raise_()

    # takeItem from source: https://stackoverflow.com/questions/23835847/how-to-remove-item-from-qlistwidget/23836142
    # the recognized gesture is given and in dependence of the gesture the action is called
    def recognizedAction(self, recognized):
        self.raiseWidgets()
        if recognized == "Circle":
            self.editToDo.setFocus()
            self.inputToDo.show()
        if recognized == "Check":
            if self.toDoList.currentItem() is not None:
                if self.tab.currentIndex() == 0:
                    self.check()
        if recognized == "Uncheck":
            if self.doneList.currentItem() is not None:
                self.uncheck()
        if recognized == "Edit":
            self.edit()

    # when check the item at the todolist is deleted and is added to the donelist
    def check(self):
        item = self.toDoList.currentItem()
        text = item.text()
        x = self.toDoList.row(item)
        self.toDoList.takeItem(x)
        newItem = QtWidgets.QListWidgetItem(text)
        newItem.setSelected(True)
        newItem.setCheckState(QtCore.Qt.Checked)
        self.doneList.insertItem(0, newItem)
        self.doneList.setCurrentItem(newItem)
        if self.toDoList.count() > 0:
            self.toDoList.setCurrentRow(0)
        self.undoRedo.updateListsCheck(newItem.text(), self.doneList.row(newItem))
        self.undoRedo.undoRedoUpdateLists()
        self.app.processEvents()

    # when uncheck, the item is deleted from the donelist and added in the todolist
    def uncheck(self):
        item = self.doneList.currentItem()
        self.undoRedo.updateListsUncheck(self.doneList.row(item), item.text())
        self.doneList.takeItem(self.doneList.row(item))
        newItem = QtWidgets.QListWidgetItem(item.text())
        newItem.setCheckState(QtCore.Qt.Unchecked)
        self.toDoList.insertItem(0, newItem)
        self.toDoList.setCurrentItem(newItem)
        if self.doneList.count() > 0:
            self.doneList.setCurrentRow(0)
        self.undoRedo.undoRedoUpdateLists()

    # when edit, the text of the current item is set in the edit popup window
    def edit(self):
        self.tabIndex = self.tab.currentIndex()
        if self.tabIndex == 0:
            self.editInput.setText(self.toDoList.currentItem().text())
            self.editIndex = self.toDoList.currentRow()
            self.editItems.show()
        if self.tabIndex == 1:
            self.editInput.setText(self.doneList.currentItem().text())
            self.editIndex = self.doneList.currentRow()
            self.editItems.show()

    # if mousepress is on the indicator of the todolist items, the current item is deleted from the
    # todolist and added to the donelist
    def checkItemOnToDoList(self, item):
        if item.checkState() == QtCore.Qt.Checked:
            self.toDoList.takeItem(self.toDoList.row(item))
            newItem = QtWidgets.QListWidgetItem(item.text())
            newItem.setCheckState(QtCore.Qt.Checked)
            self.doneList.insertItem(0, newItem)

    # if mousepress is on the indicator of the donelist items, the current item is deleted from the
    # donelist and added to the todolist
    def checkItemOnDoneList(self, item):
        if item.checkState() == QtCore.Qt.Unchecked:
            self.doneList.takeItem(self.doneList.row(item))
            newItem = QtWidgets.QListWidgetItem(item.text())
            newItem.setCheckState(QtCore.Qt.Unchecked)
            self.toDoList.insertItem(0, newItem)

    # after pressing the ok button on the input popup window a new QListWidgetItem is created
    # with the given string and inserted into todolist
    def addNewEntry(self):
        self.newEntry = self.editToDo.text()
        self.undoRedo.updateListsAddNewEntry(self.newEntry)
        self.editToDo.setText("")
        self.inputToDo.hide()
        item = QtWidgets.QListWidgetItem(self.newEntry)
        item.setCheckState(QtCore.Qt.Unchecked)
        self.toDoList.insertItem(0, item)
        self.toDoList.setCurrentItem(item)
        self.undoRedo.undoRedoUpdateLists()
        if self.tab.currentIndex() is not 0:
            self.tab.setCurrentIndex(0)

    # if a button on the input popup window is pressed the dependent function is called
    def getNewEntry(self):
        if self.sender().text() == self.okButton.text():
            if self.editToDo.text() is not "":
                self.addNewEntry()
        elif self.sender().text() == self.cancelButton.text():
            self.inputToDo.hide()
            self.editToDo.setText("")

    # the edited text of an item is set
    def addEditEntry(self):
        self.editEntry = self.editInput.text()
        self.editInput.setText("")
        self.editItems.hide()
        if self.tabIndex == 0:
            self.toDoList.currentItem().setText(self.editEntry)
        if self.tabIndex == 1:
            self.doneList.currentItem().setText(self.editEntry)
        self.undoRedo.updateListsEditEntry(self.tabIndex, self.editIndex, self.editEntry)
        self.undoRedo.undoRedoUpdateLists()

    # if a button on th edit popup window is pressed the dependent function is called
    def getEditEntry(self):
        if self.sender().text() == self.okEditButton.text():
            if self.editInput.text() is not "":
                self.addEditEntry()
        elif self.sender().text() == self.cancelEditButton.text():
            self.editInput.setText("")
            self.editItems.hide()


def main():
    app = QtWidgets.QApplication(sys.argv)
    font_db = QtGui.QFontDatabase()
    font_id = font_db.addApplicationFont("Handlee-Regular.ttf")
    handleeFont = QtGui.QFont("Handlee", 50)
    app.setFont(handleeFont)
    wiimote_connection(app)

    sys.exit(app.exec_())


def wiimote_connection(app):
    try:
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
        w = Window(wm, app)

    except Exception as e:
        print(e, ", no wiimote found")
        wm = None
        w = Window(wm, app)


if __name__ == '__main__':
    main()
