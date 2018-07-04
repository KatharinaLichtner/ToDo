#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

import wiimote
import sys
from transform import Transform
from PyQt5 import  QtWidgets, QtCore, QtGui
import wiimote_node


class Window(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.btaddr = "B8:AE:6E:1B:AD:A0"  # set some example
        # update timer
        self.wiimote = None
        self._acc_vals = []
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_all_sensors)
        self.initUI()
        self.connect_wiimote()




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



        #wiimote_node.WiimoteNode.connect_wiimote(self)
        self.show()


    def connect_wiimote(self):
        self.wm = wiimote.connect("B8:AE:6E:1B:AD:A0")

    def connect_wiimote(self):
        #self.btaddr = str(self.text.text()).strip()
        if self.wiimote is not None:
            self.wiimote.disconnect()
            self.wiimote = None
            print("connect")
           # self.connect_button.setText("connect")
            return
        if len(self.btaddr) == 17:
            print("connecting")
            #self.connect_button.setText("connecting...")
            self.wiimote = wiimote.connect(self.btaddr)
            if self.wiimote is None:
                print("try again")
                #self.connect_button.setText("try again")
            else:
             #   self.connect_button.setText("disconnect")
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
            P, DEST_W, DEST_H = (1024 /2, 768/2), 1024, 768

        #while True:
         #   if self.wm.buttons["B"]:
          #      print("Gedrückt")

            try:
                # x,y = Transform.projective_transform(P, leds, DEST_W, DEST_H)

                x, y = self.transform.transform(P, leds, DEST_W, DEST_H)
            except Exception as e:
                print(e)
                x = y = -1

            self.cursor().setPos(self.mapToGlobal(QtCore.QPoint(x,y)))


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
