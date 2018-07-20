#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets, QtCore, QtGui


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
