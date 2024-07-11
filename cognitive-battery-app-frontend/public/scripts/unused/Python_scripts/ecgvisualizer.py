# -*- coding: utf-8 -*-
"""
Created on Thu Aug 24 08:28:57 2023

@author: jrybr
"""

import sys
import serial
from PyQt5.QtWidgets import QApplication
from pyqtgraph.Qt import QtCore
import pyqtgraph as pg



class SerialPlotter():

    def __init__(self, COM_PORT):
        # Setup Serial Port
        self.ser = serial.Serial(COM_PORT, 57600)

        # Setup PyQtGraph
        self.app = QApplication([])
        self.win = pg.GraphicsLayoutWidget()
        self.win.setWindowTitle("Real-time Serial Data from " + COM_PORT)
        self.win.show()  # Ensure the window is shown

        self.plot = self.win.addPlot(title="Sensor Values over Time")
        self.curve = self.plot.plot(pen='y')
        
        self.time_data = []
        self.sensor_data = []

        # Update timer
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(4)  # Given 250Hz, update approximately every 4ms for smooth display

    def update_plot(self):
        line = self.ser.readline().decode('utf-8').strip()
        values = line.split(',')
        try:
            time_val, sensor_val = float(values[0]), float(values[1])
            
            self.time_data.append(time_val)
            self.sensor_data.append(sensor_val)
            
            if len(self.time_data) > 2500:  # Limit to last 10 seconds of data for 250Hz
                self.time_data = self.time_data[-2500:]
                self.sensor_data = self.sensor_data[-2500:]
                
            self.curve.setData(self.time_data, self.sensor_data)
        except (ValueError, IndexError):
            pass  # Skip if data cannot be converted to floats or if there's missing data

    def run(self):
        if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
            QApplication.instance().exec_()

    def close(self):
        if self.ser.is_open:
            self.ser.flush()
            self.ser.close()
    
    def closeEvent(self, event):
        self.close()
        event.accept() 

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("Usage: python ecgvisualizer.py <COM_PORT>")
        sys.exit(1)

    com_port = sys.argv[1]
    plotter = SerialPlotter(com_port)
    try:
        plotter.run()
    except KeyboardInterrupt:
        print("Interrupted! Closing the application...")
    finally:
        plotter.close()
