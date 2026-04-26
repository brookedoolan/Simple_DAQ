from PyQt6.QtWidgets import (
    QMainWindow, QHBoxLayout, QWidget,
    QVBoxLayout, QLabel, QPushButton, QGroupBox,
    QApplication, QStackedWidget, QTextEdit, QLineEdit,
    QCheckBox
)
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap
import pyqtgraph as pg

import numpy as np

from labjack_read_write import DAQ
from csv_logger import CSVLogger
import system_config
import time

pg.setConfigOption("background", "#434343")
pg.setConfigOption("foreground", "#DBDBDB")

class DAQWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Flow Test GUI")

        self.logger = CSVLogger(system_config.headers)

        self.logging_enabled = False # Log data initially off

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_gui)
        self.timer.start(50) # 20 Hz

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout()
        central.setLayout(main_layout)

        # ----------- LEFT PANEL (Labels, LJ status) -------------
        left_layout = QVBoxLayout()

        # Add image :)
        logo_label = QLabel()
        pixmap = QPixmap("images/pingu.png")
        pixmap = pixmap.scaledToWidth(250, Qt.TransformationMode.SmoothTransformation)
        logo_label.setPixmap(pixmap)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        left_layout.addWidget(logo_label)

        # Start/stop logging buttons
        log_box = QGroupBox("Data Logging")
        log_layout = QVBoxLayout()
        log_box.setLayout(log_layout)

        self.start_log_button = QPushButton("Start Logging")
        self.stop_log_button = QPushButton("Stop Logging")

        self.stop_log_button.setEnabled(False)

        log_layout.addWidget(self.start_log_button)
        log_layout.addWidget(self.stop_log_button)

        self.start_log_button.clicked.connect(self.start_logging)
        self.stop_log_button.clicked.connect(self.stop_logging)

        left_layout.addWidget(log_box)

        # Status box
        status_box = QGroupBox("Sensor Values")
        status_layout = QVBoxLayout()
        status_box.setLayout(status_layout)

        self.pt1_label = QLabel("PT1: -- bar")
        self.pt2_label = QLabel("PT2: -- bar")
        self.lctank_label = QLabel("LC_Tank: -- g")
        self.lcthrust_label = QLabel("LC_Thrust: -- g")
        #self.lc_total_label = QLabel("LC Total: -- g")
        self.flow1_label = QLabel("Flow meter 1: -- g/s")
        self.flow2_label = QLabel("Flow meter 2: -- g/s")

        self.lj_status_label = QLabel("LabJack: UNKNOWN")
        self.lj_status_label.setStyleSheet("color: orange; font-weight: bold")

        status_layout.addWidget(self.pt1_label)
        status_layout.addWidget(self.pt2_label)
        status_layout.addWidget(self.lctank_label)
        status_layout.addWidget(self.lcthrust_label)
        status_layout.addWidget(self.flow1_label)
        status_layout.addWidget(self.flow2_label)
        #status_layout.addWidget(self.lc_total_label)

        status_layout.addWidget(self.lj_status_label)

        left_layout.addWidget(status_box)


        # setpoint box
        setpoint_box = QGroupBox("Setpoints")
        setpoint_layout = QVBoxLayout()
        setpoint_box.setLayout(setpoint_layout)
        self.pt1_setpoint = QLineEdit()
        self.pt2_setpoint = QLineEdit()
        setpoint_layout.addWidget(QLabel("PT1 Setpoint (bar)"))
        setpoint_layout.addWidget(self.pt1_setpoint)
        setpoint_layout.addWidget(QLabel("PT2 Setpoint (bar)"))
        setpoint_layout.addWidget(self.pt2_setpoint)
        left_layout.addWidget(setpoint_box)

        main_layout.addLayout(left_layout, 1)
        left_layout.addStretch()



        # --------- RIGHT PANEL (Graphs) -------------------
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 3)

        # Pressure plot
        self.pressure_plot = pg.PlotWidget(title="Pressure")
        self.pressure_plot.setLabel("left", "Pressure", units="bar")
        self.pressure_plot.setLabel("bottom", "Time", units="s")
        self.pressure_plot.setXRange(-60, 0)
        self.pressure_curve1 = self.pressure_plot.plot(pen=pg.mkPen("r", width=2), name="PT1")
        self.pressure_curve2 = self.pressure_plot.plot(pen=pg.mkPen("g", width=2), name="PT2")
        self.pressure_setpoint1 = self.pressure_plot.plot(pen=pg.mkPen("r", style=Qt.PenStyle.DashLine), name="PT1 Setpoint")
        self.pressure_setpoint2 = self.pressure_plot.plot(pen=pg.mkPen("g", style=Qt.PenStyle.DashLine), name="PT2 Setpoint")

        pressure_section = QHBoxLayout()
        pressure_section.addWidget(self.pressure_plot, 4)
        legend_layout = QVBoxLayout()
        pressure_section.addLayout(legend_layout, 1)

        self.pt1_checkbox = QCheckBox("PT1")
        self.pt1_checkbox.setChecked(True)

        self.pt2_checkbox = QCheckBox("PT2")
        self.pt2_checkbox.setChecked(True)

        legend_layout.addWidget(self.pt1_checkbox)
        legend_layout.addWidget(self.pt2_checkbox)

        legend_layout.addStretch()

        right_layout.addLayout(pressure_section)

        self.pt1_checkbox.stateChanged.connect(
            lambda state: self.pressure_curve1.setVisible(state == 2)
        )

        self.pt2_checkbox.stateChanged.connect(
            lambda state: self.pressure_curve2.setVisible(state == 2)
        )

        self.pressure_plot.enableAutoRange(axis='y')

        # Load cell plot
        self.load_plot = pg.PlotWidget(title="Load Cells")
        self.load_plot.setLabel("left", "Mass", units='g')
        self.load_plot.setLabel("bottom", 'Time', units='s')
        self.load_plot.setXRange(-60, 0)
        self.load_curvetank = self.load_plot.plot(pen=pg.mkPen("c", width=2), name="LC_Tank")
        self.load_curvethrust = self.load_plot.plot(pen=pg.mkPen("y", width=2), name="LC_Thrust")
        #self.load_curve_total = self.load_plot.plot(pen=pg.mkPen("b", width=2), name="LC_Total")

        load_cell_section = QHBoxLayout()
        load_cell_section.addWidget(self.load_plot, 4)
        legend_layout_LC = QVBoxLayout()
        load_cell_section.addLayout(legend_layout_LC,1)

        self.lctank_checkbox = QCheckBox("LC_Tank")
        self.lctank_checkbox.setChecked(True)

        self.lcthrust_checkbox = QCheckBox("LC_Thrust")
        self.lcthrust_checkbox.setChecked(True)

        #self.lc_total_checkbox = QCheckBox("LC_Total")
        #self.lc_total_checkbox.setChecked(True)

        legend_layout_LC.addWidget(self.lctank_checkbox)
        legend_layout_LC.addWidget(self.lcthrust_checkbox)
        #legend_layout_LC.addWidget(self.lc_total_checkbox)

        legend_layout_LC.addStretch()

        right_layout.addLayout(load_cell_section)

        self.lctank_checkbox.stateChanged.connect(
            lambda state: self.load_curvetank.setVisible(state == 2)
        )

        self.lcthrust_checkbox.stateChanged.connect(
            lambda state: self.load_curvethrust.setVisible(state == 2)
        )

        #self.lc_total_checkbox.stateChanged.connect(
        #    lambda state: self.load_curve_total.setVisible(state == 2)
        #)

        self.load_plot.enableAutoRange(axis='y')

        # Flow meter plot
        self.flow_plot = pg.PlotWidget(title="Flow Meter")
        self.flow_plot.setLabel("left", "Flowrate", units="g/s")
        self.flow_plot.setLabel("bottom", "Time", units="s")
        self.flow_plot.setXRange(-60, 0)
        self.flow_curve1 = self.flow_plot.plot(pen=pg.mkPen("r", width=2), name="Flow1")
        self.flow_curve2 = self.flow_plot.plot(pen=pg.mkPen("g", width=2), name="Flow2")

        flow_section = QHBoxLayout()
        flow_section.addWidget(self.flow_plot,4)
        legend_layout_flow = QVBoxLayout()
        flow_section.addLayout(legend_layout_flow, 1)

        self.flow1_checkbox = QCheckBox("Flow1")
        self.flow1_checkbox.setChecked(True)

        self.flow2_checkbox = QCheckBox("Flow2")
        self.flow2_checkbox.setChecked(True)

        legend_layout_flow.addWidget(self.flow1_checkbox)
        legend_layout_flow.addWidget(self.flow2_checkbox)

        legend_layout_flow.addStretch()

        right_layout.addLayout(flow_section)

        self.flow1_checkbox.stateChanged.connect(
            lambda state: self.flow_curve1.setVisible(state == 2)
        )

        self.flow2_checkbox.stateChanged.connect(
            lambda state: self.flow_curve2.setVisible(state == 2)
        )

        self.flow_plot.enableAutoRange(axis='y')


        # Data storage
        self.start_time = time.time()

        self.time_data = np.array([])
        self.pt1_data = []
        self.pt2_data = []

        self.lctank_data = []
        self.lcthrust_data = []
        #self.lc_total_data = []

        self.flow1_data = []
        self.flow2_data = []


        # DAQ - Read labjacks
        self.daq = DAQ()

    def update_gui(self):

        try:
            pt1, pt2, lc_tank, lc_thrust, flow1, flow2 = self.daq.read_sensors()
            #lc_total = lc_tank + lc_thrust
            if self.daq.connected:
                self.lj_status_label.setText("Labjack CONNECTED")
                self.lj_status_label.setStyleSheet("color: #00E676; font-weight: bold")
            else:
                self.lj_status_label.setText("LabJack DISCONNECTED: Simulation Mode")
                self.lj_status_label.setStyleSheet("color: orange; font-weight: bold")

        except Exception as e:

            print(f"ERROR [{type(e).__name__}]: {e}")

            self.lj_status_label.setText("LabJack DISCONNECTED")
            self.lj_status_label.setStyleSheet("color: red; font-weight: bold")

            return

        now = time.time()
        t = now - self.start_time
        self.start_time = now

        # Append to current data storage
        self.time_data -= t
        self.time_data = np.append(self.time_data, 0.0)
        self.pt1_data.append(pt1)
        self.pt2_data.append(pt2)

        self.lctank_data.append(lc_tank)
        self.lcthrust_data.append(lc_thrust)
        #self.lc_total_data.append(lc_total)

        self.flow1_data.append(flow1)
        self.flow2_data.append(flow2)

        # Limit data size
        MAX_POINTS = 1000

        if len(self.time_data) > MAX_POINTS:
            self.time_data = self.time_data[-MAX_POINTS:]
            self.pt1_data = self.pt1_data[-MAX_POINTS:]
            self.pt2_data = self.pt2_data[-MAX_POINTS:]
            self.lctank_data = self.lctank_data[-MAX_POINTS:]
            self.lcthrust_data = self.lcthrust_data[-MAX_POINTS:]
            #self.lc_total_data = self.lc_total_data[-MAX_POINTS:]
            self.flow1_data = self.flow1_data[-MAX_POINTS:]
            self.flow2_data = self.flow2_data[-MAX_POINTS:]


        # Write to CSV (only if logging data enabled)
        if self.logging_enabled:
            self.logger.write_row([pt1, pt2, lc_tank, lc_thrust, flow1, flow2])

        # Update plots
        self.pressure_curve1.setData(self.time_data, self.pt1_data)
        self.pressure_curve2.setData(self.time_data, self.pt2_data)

        self.load_curvetank.setData(self.time_data, self.lctank_data)
        self.load_curvethrust.setData(self.time_data, self.lcthrust_data)
        #self.load_curve_total.setData(self.time_data, self.lc_total_data)

        self.flow_curve1.setData(self.time_data, self.flow1_data)
        self.flow_curve2.setData(self.time_data, self.flow2_data)


        # update setpoint lines
        try:
            pt1_setpoint = float(self.pt1_setpoint.text())
            self.pressure_setpoint1.setData([-60, 0], [pt1_setpoint, pt1_setpoint])
        except ValueError:
            self.pressure_setpoint1.setData([], [])

        try:
            pt2_setpoint = float(self.pt2_setpoint.text())
            self.pressure_setpoint2.setData([-60, 0], [pt2_setpoint, pt2_setpoint])
        except ValueError:
            self.pressure_setpoint2.setData([], [])

        # Update data labels
        self.pt1_label.setText(f"PT1: {pt1:.2f} bar")
        self.pt2_label.setText(f"PT2: {pt2:.2f} bar")

        self.lctank_label.setText(f"LC Tank: {lc_tank:.5f} g")
        self.lcthrust_label.setText(f"LC Thrust: {lc_thrust:.5f} g")
        #self.lc_total_label.setText(f"LC Total: {lc_total:.1f} g")

        self.flow1_label.setText(f"Flow meter: {flow1:.2f} g/s")
        self.flow2_label.setText(f"Flow meter: {flow2:.2f} g/s")

    def start_logging(self):
        self.logging_enabled = True
        self.start_log_button.setEnabled(False)
        self.stop_log_button.setEnabled(True)
        print("Logging started")

    def stop_logging(self):
        self.logging_enabled = False
        self.start_log_button.setEnabled(True)
        self.stop_log_button.setEnabled(False)
        print("Logging stopped")