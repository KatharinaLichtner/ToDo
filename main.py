#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

import wiimote
import sys
from transform import Transform
from PyQt5 import  QtWidgets, QtCore, QtGui


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
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
        item = QtWidgets.QListWidgetItem("Hallo")
        item.setCheckState(0)
        self.toDoList.addItem(item)

        # listWidget DoneList
        self.doneList = QtWidgets.QListWidget()
        self.doneList.setStyleSheet("background-color: white")
        self.doneList.setStyleSheet("QListWidget::indicator:checked{image: url(checked.svg)}")
        #self.doneList.setStyleSheet("color: black")
        layoutListDoneWidget = QtWidgets.QHBoxLayout()
        layoutListDoneWidget.addWidget(self.doneList)
        tabDone.setLayout(layoutListDoneWidget)
        item = QtWidgets.QListWidgetItem("Done")
        item.setCheckState(2)
        self.doneList.addItem(item)

        layoutList.addWidget(self.tab)

        # init Popup
        self.inputToDo = QtWidgets.QWidget()
        layoutPopup = QtWidgets.QVBoxLayout()
        layoutInput = QtWidgets.QVBoxLayout()
        layoutButtons = QtWidgets.QHBoxLayout()
        self.inputToDo.setWindowTitle("New To Do")
        labelInput = QtWidgets.QLabel("Type in new To Do:")
        self.editToDo = QtWidgets.QLineEdit()
        self.okButton = QtWidgets.QPushButton("OK")
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        layoutInput.addWidget(labelInput)
        layoutInput.addWidget(self.editToDo)
        layoutButtons.addWidget(self.cancelButton)
        layoutButtons.addWidget(self.okButton)
        layoutButtons.setAlignment(QtCore.Qt.AlignBottom)
        layoutPopup.addLayout(layoutInput)
        layoutPopup.addLayout(layoutButtons)
        self.inputToDo.setLayout(layoutPopup)
        #self.inputToDo.show()

        # adding layouts tab und Settings to window
        layout.addLayout(layoutSettings)
        layout.addLayout(layoutList)
        self.window().setLayout(layout)
        self.show()


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
