from PyQt6.QtWidgets import ( 
    QMainWindow, QHBoxLayout, QWidget,  
    QVBoxLayout, QLabel, QPushButton, QGroupBox, 
    QApplication, QStackedWidget, QTextEdit, QLineEdit, 
    QCheckBox 
) 
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QPixmap
import pyqtgraph as pg

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
        self.lc1_label = QLabel("LC1: -- kg")
        self.lc2_label = QLabel("LC2: -- kg")
        self.flow1_label = QLabel("Flow meter 1: -- kg/s")
        self.flow2_label = QLabel("Flow meter 2: -- kg/s")

        self.lj_status_label = QLabel("LabJack: UNKNOWN")
        self.lj_status_label.setStyleSheet("color: orange; font-weight: bold")
        
        status_layout.addWidget(self.pt1_label)
        status_layout.addWidget(self.pt2_label)
        status_layout.addWidget(self.lc1_label)
        status_layout.addWidget(self.lc2_label)
        status_layout.addWidget(self.flow1_label)
        status_layout.addWidget(self.flow2_label)

        status_layout.addWidget(self.lj_status_label)

        left_layout.addWidget(status_box)
        left_layout.addStretch()

        main_layout.addLayout(left_layout, 1)

        # --------- RIGHT PANEL (Graphs) -------------------
        right_layout = QVBoxLayout()
        main_layout.addLayout(right_layout, 3)

        # Pressure plot
        self.pressure_plot = pg.PlotWidget(title="Pressure")
        self.pressure_plot.setLabel("left", "Pressure", units="bar")
        self.pressure_plot.setLabel("bottom", "Time", units="s")
        self.pressure_curve1 = self.pressure_plot.plot(pen=pg.mkPen("r", width=2), name="PT1")
        self.pressure_curve2 = self.pressure_plot.plot(pen=pg.mkPen("g", width=2), name="PT2")

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
        self.load_plot.setLabel("left", "Mass", units='kg')
        self.load_plot.setLabel("bottom", 'Time', units='s')
        self.load_curve1 = self.load_plot.plot(pen=pg.mkPen("c", width=2), name="LC1")
        self.load_curve2 = self.load_plot.plot(pen=pg.mkPen("y", width=2), name="LC2")

        load_cell_section = QHBoxLayout()
        load_cell_section.addWidget(self.load_plot, 4)
        legend_layout_LC = QVBoxLayout()
        load_cell_section.addLayout(legend_layout_LC,1)

        self.lc1_checkbox = QCheckBox("LC1")
        self.lc1_checkbox.setChecked(True)

        self.lc2_checkbox = QCheckBox("LC2")
        self.lc2_checkbox.setChecked(True)

        legend_layout_LC.addWidget(self.lc1_checkbox)
        legend_layout_LC.addWidget(self.lc2_checkbox)

        legend_layout_LC.addStretch()

        right_layout.addLayout(load_cell_section)

        self.lc1_checkbox.stateChanged.connect(
            lambda state: self.load_curve1.setVisible(state == 2)
        )

        self.lc2_checkbox.stateChanged.connect(
            lambda state: self.load_curve2.setVisible(state == 2)
        )

        self.load_plot.enableAutoRange(axis='y')

        # Flow meter plot
        self.flow_plot = pg.PlotWidget(title="Flow Meter")
        self.flow_plot.setLabel("left", "Flowrate", units="kg/s")
        self.flow_plot.setLabel("bottom", "Time", units="s")
        self.flow_curve1 = self.flow_plot.plot(pen=pg.mkPen("c", width=2), name="Flow1")
        self.flow_curve2 = self.flow_plot.plot(pen=pg.mkPen("b", width=2), name="Flow2")

        flow_section = QHBoxLayout()
        flow_section.addWidget(self.flow_plot,4)
        legend_layout_flow = QVBoxLayout()
        flow_section.addLayout(legend_layout_flow, 1)

        self.flow_checkbox = QCheckBox("Flow1")
        self.flow_checkbox.setChecked(True)

        self.flow_checkbox = QCheckBox("Flow2")
        self.flow_checkbox.setChecked(True)

        legend_layout_flow.addWidget(self.flow_checkbox)

        legend_layout_flow.addStretch()

        right_layout.addLayout(flow_section)

        self.flow_checkbox.stateChanged.connect(
            lambda state: self.flow_curve1.setVisible(state == 2)
        )

        self.flow_checkbox.stateChanged.connect(
            lambda state: self.flow_curve2.setVisible(state == 2)
        )

        self.flow_plot.enableAutoRange(axis='y')


        # Data storage
        self.start_time = time.time()

        self.time_data = []
        self.pt1_data = []
        self.pt2_data = []

        self.lc1_data = []
        self.lc2_data = []

        self.flow1_data = []
        self.flow2_data = []


        # DAQ - Read labjacks
        self.daq = DAQ()

    def update_gui(self):

        try: 
            pt1, pt2, lc1, lc2, flow1, flow2 = self.daq.read_sensors()
            if self.daq.connected:
                self.lj_status_label.setText("Labjack CONNECTED")
                self.lj_status_label.setStyleSheet("color: #00E676; font-weight: bold")
            else:
                self.lj_status_label.setText("LabJack DISCONNECTED: Simulation Mode")
                self.lj_status_label.setStyleSheet("color: orange; font-weight: bold")

        except Exception as e:

            print("ERROR:", e)

            self.lj_status_label.setText("LabJack DISCONNECTED")
            self.lj_status_label.setStyleSheet("color: red; font-weight: bold")

            return
        
        t = time.time() - self.start_time
        
        # Append to current data storage 
        self.time_data.append(t)
        self.pt1_data.append(pt1)
        self.pt2_data.append(pt2)

        self.lc1_data.append(lc1)
        self.lc2_data.append(lc2)

        self.flow1_data.append(flow1)
        self.flow2_data.append(flow2)

        # Limit data size 
        MAX_POINTS = 1000

        if len(self.time_data) > MAX_POINTS:
            self.time_data = self.time_data[-MAX_POINTS:]
            self.pt1_data = self.pt1_data[-MAX_POINTS:]
            self.pt2_data = self.pt2_data[-MAX_POINTS:]
            self.lc1_data = self.lc1_data[-MAX_POINTS:]
            self.lc2_data = self.lc2_data[-MAX_POINTS:]
            self.flow1_data = self.flow1_data[-MAX_POINTS:]
            self.flow2_data = self.flow2_data[-MAX_POINTS:]
        
        # Write to CSV (only if logging data enabled)
        if self.logging_enabled:
            self.logger.write_row([pt1, pt2, lc1, lc2, flow1, flow2])

        # Update plots
        self.pressure_curve1.setData(self.time_data, self.pt1_data)
        self.pressure_curve2.setData(self.time_data, self.pt2_data)

        self.load_curve1.setData(self.time_data, self.lc1_data)
        self.load_curve2.setData(self.time_data, self.lc2_data)

        self.flow_curve1.setData(self.time_data, self.flow1_data)
        self.flow_curve2.setData(self.time_data, self.flow2_data)

        # Update data labels
        self.pt1_label.setText(f"PT1: {pt1:.2f} bar")
        self.pt2_label.setText(f"PT2: {pt2:.2f} bar")

        self.lc1_label.setText(f"LC1: {lc1:.1f} N")
        self.lc2_label.setText(f"LC2: {lc2:.1f} N")

        self.flow1_label.setText(f"Flow meter: {flow1:.2f} kg/s")
        self.flow2_label.setText(f"Flow meter: {flow2:.2f} kg/s")

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