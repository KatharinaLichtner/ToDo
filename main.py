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
        self.btaddr = "B8:AE:6E:1B:AD:A0"
        self.wiimote = None
        self._acc_vals = []
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_all_sensors)
        self.initUI()
        try:
            self.connect_wiimote()
        except Exception as e:
            print(e, ", no wiimote found")

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
        self.setGeometry(0, 0, 640, 720)
        self.window().setStyleSheet("background-color: white")

        layout = QtWidgets.QVBoxLayout()
        layoutSettings = QtWidgets.QHBoxLayout()
        layoutList = QtWidgets.QHBoxLayout()

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

        # listWidget ToDoList
        # transparent background from source https://stackoverflow.com/questions/27497209/how-to-make-a-qwidget-based-
        # window-have-a-transparent-background
        self.toDoList = QtWidgets.QListWidget()
        layoutListToDoWidget = QtWidgets.QHBoxLayout()

        self.drawGestures = QtWidgets.QWidget()
        #self.drawGestures.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        #self.drawGestures.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.drawGestures.setStyleSheet("background-color: green")
        self.drawGestures.setMouseTracking(True)
        layout.addWidget(self.drawGestures)

        layoutListToDoWidget.addWidget(self.toDoList)
        self.tabToDo.setLayout(layoutListToDoWidget)
        #self.tabToDo.setStyleSheet("background-color: green")
        self.toDoList.setStyleSheet("background-color: blue")
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
        self.show()
        self.drawGestures.show()
        self.drawGestures.activateWindow()
        self.drawGestures.raise_()

    def connect_wiimote(self):
        self.wiimote = wiimote.connect(self.btaddr)

        if self.wiimote is not None:
            self.wiimote.ir.register_callback(self.process_wiimote_ir_data)
            self.wiimote.buttons.register_callback(self.getPressedButton)
            self.set_update_rate(30)

    # gets which button was pressed on the wiimote
    def getPressedButton(self, ev):
        x = self.cursor().pos().x()
        y = self.cursor().pos().y()

        # if the undo or the redo buttons were clicked while pressing the 'A'-Button on the wiimote, the action is
        if self.wiimote.buttons["A"]:
            xUndo = self.undoButton.pos().x()
            yUndo = self.undoButton.pos().x()
            xRedo = self.redoButton.pos().x()
            yRedo = self.redoButton.pos().y()
            if x > xUndo and x < xUndo + self.undoButton.width() and y > yUndo and y < yUndo + self.undoButton.height():
                self.undo()

            elif x > xRedo and x < xRedo + self.redoButton.width() and y > yRedo and y < yRedo + self.redoButton.height():
                self.redo()

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
        if len(self.pos) == 0:
            print("no gesture made")
        else:
            if event.button() == QtCore.Qt.LeftButton:
                self.draw = False
                recognized = self.recognizer.recognizeGesture(self.pos)
                self.recognizedAction(recognized)
                self.pos = []
                self.update()

    # takeItem from source: https://stackoverflow.com/questions/23835847/how-to-remove-item-from-qlistwidget/23836142
    def recognizedAction(self, recognized):
        if recognized == "Circle":
            self.inputToDo.show()
        if recognized == "Check":
            item = self.toDoList.currentItem()
            self.toDoList.takeItem(self.toDoList.row(item))
            newItem = QtWidgets.QListWidgetItem(item.text())
            newItem.setCheckState(2)
            self.doneList.addItem(newItem)

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
