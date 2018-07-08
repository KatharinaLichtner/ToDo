#!/usr/bin/env python3
# coding: utf-8
# -*- coding: utf-8 -*-


#by Miriam Schlindwein

from pyqtgraph.flowchart import Flowchart, Node
from pyqtgraph.flowchart.library.common import CtrlNode
import pyqtgraph.flowchart.library as fclib
from pyqtgraph.Qt import QtGui, QtCore
from scipy import fft
from sklearn import svm
import pyqtgraph as pg
import numpy as np
import wiimote_node
import wiimote


class FftNode(CtrlNode):
    """
    FftNode reads in the accelerometer data of x-,y- and z-axis.
    A spectogram after fourier transformation is returned.
    """
    nodeName = "Fft"
    uiTemplate = [
        ('size',  'spin', {'value': 32.0, 'step': 1.0, 'bounds': [0.0, 128.0]}),
    ]

    def __init__(self, name):
        terminals = {
            'dataInX': dict(io='in'),
            'dataInY': dict(io='in'),
            'dataInZ': dict(io='in'),
            'dataOut': dict(io='out'),
        }
        self._bufferx = np.array([])
        self._buffery = np.array([])
        self._bufferz = np.array([])

        CtrlNode.__init__(self, name, terminals=terminals)

    # fourier transformation with the incoming data and returns a spectogram
    def process(self, **kwds):
        size = int(self.ctrls['size'].value())
        self._bufferx = np.append(self._bufferx, kwds['dataInX'])
        self._bufferx = self._bufferx[-size:]

        self._buffery = np.append(self._buffery, kwds['dataInY'])
        self._buffery = self._buffery[-size:]

        self._bufferz = np.append(self._bufferz, kwds['dataInZ'])
        self._bufferz = self._bufferz[-size:]

        x = np.fft.fft(self._bufferx) / len(self._bufferx)
        x = abs(x)
        y = np.fft.fft(self._buffery) / len(self._buffery)
        y = abs(y)
        z = np.fft.fft(self._bufferz) / len(self._bufferz)
        z = abs(z)
        signal = np.array([])
        for i in range(len(x)):
            signal = np.append(signal, (x[i] + y[i] + z[i]) / 3)
        signal = signal[1:len(signal)//2]
        return {'dataOut': signal}


fclib.registerNodeType(FftNode, [('Data',)])


class SvmNode(Node):
    """
    SvmNode is the machine learning module. With the widget the user can decide the kind of input
    and define the mode between 'training', 'prediction' and 'inaktive'. The kind of input are 'shake',
    'swing' and 'bump'. After choosing the mode, the given data is proceed like the chosen.
    If training the machine is trained to the selected kind. After training
    predicition of the input data is possible.
    """
    nodeName = "Svm"

    def __init__(self, name):
        terminals = {
            'dataIn': dict(io='in'),
            'dataOut': dict(io='out'),
        }
        self.shake = 0
        self.swing = 1
        self.bump = 2
        self.mode = "inactive"
        self.category = "Shake"
        self.training_data = []
        self.data = []
        self.c = svm.SVC()
        self.feature_vector = []
        self.timer = QtCore.QTime()

        # init the UI for the node
        self.ui = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()

        label = QtGui.QLabel("Choose category: \n" "Shake, Swing or Bump:")
        self.layout.addWidget(label)

        self.categoryItem = QtGui.QComboBox()
        self.categoryItem.addItem("Shake")
        self.categoryItem.addItem("Swing")
        self.categoryItem.addItem("Bump")

        self.layout.addWidget(self.categoryItem)

        label2 = QtGui.QLabel("Choose mode")
        self.layout.addWidget(label2)

        self.training_button = QtGui.QPushButton("training")
        self.training_button.clicked.connect(self.clicked_button)
        self.training_button.setStyleSheet('QPushButton {background-color: white; color: black;}')
        self.layout.addWidget(self.training_button)
        self.prediction_button = QtGui.QPushButton("prediction")
        self.prediction_button.clicked.connect(self.clicked_button)
        self.prediction_button.setStyleSheet('QPushButton {background-color: white; color: black;}')
        self.layout.addWidget(self.prediction_button)
        self.inactive_button = QtGui.QPushButton("inactive")
        self.inactive_button.setStyleSheet('QPushButton {background-color: black; color: white;}')
        self.inactive_button.clicked.connect(self.clicked_button)
        self.layout.addWidget(self.inactive_button)
        self.ui.setLayout(self.layout)

        Node.__init__(self, name, terminals=terminals)

    def ctrlWidget(self):
        return self.ui

    def clicked_button(self):
        """
        when a button is pressed the mode and category is selected and the pressed button is colored
        how long the time the training or prediction lasts.
        when training or predicition the timer starts to read the input data
        """
        self.mode = self.sender().text()
        self.sender().setStyleSheet('QPushButton {background-color: black; color: white;}')
        self.inactive_button.setStyleSheet('QPushButton {background-color: white; color: black;}')
        if self.mode == "training":
            self.category = self.categoryItem.currentText()

        if self.mode is not "inactive":
            self.timer.start()

    def process(self, **kwds):
        """
        while the timer is running:
        if mode is training the feature vector is expanded with the defined category.
        if mode is prediction the input data in the time during timer is read in and then
        with the classifier the category is predicted.
        When timer stops the selected button is removed and inactive is selected.
        """
        output = []

        if self.timer.elapsed() < 5000:
            self.data = kwds['dataIn']
            if self.mode == "training":
                if self.category == "Shake":
                    self.feature_vector.append(self.shake)
                elif self.category == "Swing":
                    self.feature_vector.append(self.swing)
                else:
                    self.feature_vector.append(self.bump)
                self.training_data.append(self.data[1:])
                self.c.fit(self.training_data, self.feature_vector)

            elif self.mode == "prediction":
                print("prediction")
                output = self.c.predict([self.data[1:]])

        self.timer.elapsed()
        self.training_button.setStyleSheet('QPushButton {background-color: white; color: black;}')
        self.prediction_button.setStyleSheet('QPushButton {background-color: white; color: black;}')
        self.inactive_button.setStyleSheet('QPushButton {background-color: black; color: white;}')
        return {'dataOut': output}


fclib.registerNodeType(SvmNode, [('Signal',)])


class DisplayTextNode(Node):
    """
    displays the predicted category from the svm-Node
    """
    nodeName = "TextNode"

    def __init__(self, name):
        terminals = {
             'dataIn': dict(io='in'),
             'dataOut': dict(io='out'),
        }
        self.shake = 0
        self.swing = 1
        self.bump = 2

        # init UI
        self.ui = QtGui.QWidget()
        self.layout = QtGui.QGridLayout()

        label = QtGui.QLabel("Predicted category:")
        self.layout.addWidget(label)

        self.prediction = QtGui.QLabel("")
        self.layout.addWidget(self.prediction)
        self.ui.setLayout(self.layout)

        Node.__init__(self, name, terminals=terminals)

    def ctrlWidget(self):
        return self.ui

    def process(self, **kwds):
        """
        when 'shake' is predicted the text is displayed in the label.
        This also applies to the other one.
        """
        input = kwds['dataIn']
        if len(input) is not 0:
            if input[0] == self.shake:
                print("Shake")
                self.prediction.setText("Shake")
            elif input[0] == self.swing:
                print("Swing")
                self.prediction.setText("Swing")
            else:
                print("bump")
                self.prediction.setText("Bump")

        return {"dataOut": None}


fclib.registerNodeType(DisplayTextNode, [('data',)])

if __name__ == '__main__':
    import sys
    app = QtGui.QApplication([])
    win = QtGui.QMainWindow()
    win.setWindowTitle('Activity Recognizer')
    cw = QtGui.QWidget()
    win.setCentralWidget(cw)
    layout = QtGui.QGridLayout()
    cw.setLayout(layout)

    # Create an empty flowchart with a single input and output
    fc = Flowchart(terminals={
    })
    w = fc.widget()

    layout.addWidget(fc.widget(), 0, 0, 2, 1)

    # creates PlotWidgets for all plotted data
    pw1 = pg.PlotWidget(name='PlotWidgetX')
    layout.addWidget(pw1, 0, 1)
    pw1.setYRange(0, 1024)

    pw1Node = fc.createNode('PlotWidget', pos=(0, -150))
    pw1Node.setPlot(pw1)

    pw2 = pg.PlotWidget(name='PlotWidgetY')
    layout.addWidget(pw2, 1, 1)
    pw2.setYRange(0, 1024)

    pw2Node = fc.createNode('PlotWidget', pos=(110, -150))
    pw2Node.setPlot(pw2)

    pw3 = pg.PlotWidget(name='PlotWidgetZ')
    layout.addWidget(pw3, 0, 2)
    pw3.setYRange(0, 1024)

    pw3Node = fc.createNode('PlotWidget', pos=(220, -150))
    pw3Node.setPlot(pw3)

    pw4 = pg.PlotWidget(name='PlotWidgetFft')
    layout.addWidget(pw4, 1, 2)
    pw4.setYRange(0, 1024)

    pw4Node = fc.createNode('PlotWidget', pos=(330, -150))
    pw4Node.setPlot(pw4)

    # create all nodes
    wiimoteNode = fc.createNode('Wiimote', pos=(0, 0), )
    bufferNodeX = fc.createNode('Buffer', pos=(0, 150))
    bufferNodeY = fc.createNode('Buffer', pos=(110, 150))
    bufferNodeZ = fc.createNode('Buffer', pos=(220, 150))
    fftNode = fc.createNode('Fft', pos=(220, 300))
    svmNode = fc.createNode('Svm', pos=(330, 150))
    textNode = fc.createNode("TextNode", pos=(330, 300))

    fc.connectTerminals(wiimoteNode['accelX'], bufferNodeX['dataIn'])
    fc.connectTerminals(wiimoteNode['accelY'], bufferNodeY['dataIn'])
    fc.connectTerminals(wiimoteNode['accelZ'], bufferNodeZ['dataIn'])

    fc.connectTerminals(bufferNodeX['dataOut'], fftNode['dataInX'])
    fc.connectTerminals(bufferNodeY['dataOut'], fftNode['dataInY'])
    fc.connectTerminals(bufferNodeZ['dataOut'], fftNode['dataInZ'])

    fc.connectTerminals(bufferNodeX['dataOut'], pw1Node['In'])
    fc.connectTerminals(bufferNodeY['dataOut'], pw2Node['In'])
    fc.connectTerminals(bufferNodeZ['dataOut'], pw3Node['In'])
    fc.connectTerminals(fftNode['dataOut'], pw4Node['In'])

    fc.connectTerminals(fftNode['dataOut'], svmNode['dataIn'])
    fc.connectTerminals(svmNode['dataOut'], textNode['dataIn'])
    win.show()
    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
        QtGui.QApplication.instance().exec_()
