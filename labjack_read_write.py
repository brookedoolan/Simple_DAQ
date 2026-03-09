from labjack import ljm
import system_config
import time

import random

class DAQ:

    def __init__(self):
        try:
            self.handle = ljm.openS("T7", "USB", "ANY")
            self.connected = True
            print("LabJack connected")
        except Exception as e:
            print("LabJack not found, running in sim mode")
            self.connected = False
            self.handle = None

        if self.connected:
            # Load cells
            # Configure differential load cell channel
            ljm.eWriteName(self.handle, "AIN2_NEGATIVE_CH", 3)
            ljm.eWriteName(self.handle, "AIN4_NEGATIVE_CH", 5)
            # Small range for better resolution
            ljm.eWriteName(self.handle, "AIN2_RANGE", 0.01) # +/- 0.1V
            ljm.eWriteName(self.handle, "AIN4_RANGE", 0.01)

            # Higher resolution
            ljm.eWriteName(self.handle, "AIN_ALL_RESOLUTION_INDEX", 12)
            # Stream safe settling time
            ljm.eWriteName(self.handle, "AIN_ALL_SETTLING_US", 100)

            # Flow meters

            # FLOW 1 (FIO0)
            ljm.eWriteName(self.handle, "DIO0_EF_ENABLE", 0)
            ljm.eWriteName(self.handle, "DIO0_EF_INDEX", 7)  # Counter
            #ljm.eWriteName(self.handle, "DIO0_EF_ENABLE", 1)

            # FLOW 2 (FIO2)
            ljm.eWriteName(self.handle, "DIO2_EF_ENABLE", 0)
            ljm.eWriteName(self.handle, "DIO2_EF_INDEX", 7)
            #ljm.eWriteName(self.handle, "DIO2_EF_ENABLE", 1)

            # Reset counters
            #ljm.eWriteName(self.handle, "DIO0_EF_READ_A_AND_RESET", 0)
            #ljm.eWriteName(self.handle, "DIO2_EF_READ_A_AND_RESET", 0)

            self.last_time = time.time()
            self.last_flow1 = 0
            self.last_flow2 = 0
            self.flow1_pulses = 0
            self.flow2_pulses = 0

        self.names = [
            system_config.PT1,
            system_config.PT2,
            system_config.LC1,
            system_config.LC2,
            system_config.FLOW1,
            system_config.FLOW2
        ]

    # Labjack read tasks
    def read_sensors(self):

        if not self.connected:
            pt1 = 1.2 + random.uniform(-0.02, 0.02)
            pt2 = 1.1 + random.uniform(-0.02, 0.02)
            lc1 = random.uniform(0, 5)
            lc2 = random.uniform(0, 5)

            flow1 = random.uniform(0, 10)
            flow2 = random.uniform(0, 10)

            flow1_count = random.uniform(0, 10)
            flow2_count = random.uniform(0, 10)

            lc_total = lc1 + lc2

            return pt1, pt2, lc1, lc2, lc_total, flow1, flow2, flow1_count, flow2_count

        values = ljm.eReadNames(self.handle, len(self.names), self.names)
        pt1_v, pt2_v, lc1_v, lc2_v, flow1_count, flow2_count = values

        # Convert readings. Gauge -> absolute readings
        P_atm = 1.013 # atmospheric pressure in bar
        # CURRENTLY FOR 500 PSI SENSOR
        pt1 = ((pt1_v - 0.5)*150/4)*0.06895 + P_atm # psi to bar
        pt2 = ((pt2_v - 0.5)*150/4)*0.06895 + P_atm

        # CALIBRATE
        lc1 = lc1_v*10000
        lc2 = lc2_v*10000

        lc_total = lc1_v + lc2_v
        lc_total = 1098.6309573550288*lc_total - 11.092479241981106
        lc1 = lc2 = lc_total

        # CALIBRATE

        now = time.time()
        dt = now - self.last_time
        self.last_time = now


        flow1_freq = (flow1_count - self.last_flow1)/dt
        flow2_freq = (flow2_count - self.last_flow2)/dt

        self.last_flow1 = flow1_count
        self.last_flow2 = flow2_count

        flow1_L_min = flow1_freq/11 # L/min
        flow2_L_min = flow2_freq/11

        flow1 = flow1_L_min/60 # L/min to kg/s
        flow2 = flow2_L_min/60

        """
        # Manually counting
        thresh = 0.5
        if flow1_count > thresh and self.last_flow1 <= thresh:
            self.flow1_pulses += 1
        if flow2_count > thresh and self.last_flow2 <= thresh:
            self.flow2_pulses += 1

        freq1 = self.flow1_pulses/dt
        freq2 = self.flow2_pulses/dt

        self.flow1_pulses = 0
        self.flow2_pulses = 0

        self.last_flow1 = flow1_count
        self.last_flow2 = flow2_count

        flow1_Lmin = freq1/11
        flow2_Lmin = freq2/11

        flow1 = flow1_Lmin/60
        flow2 = flow2_Lmin/60
        """
        return pt1, pt2, lc1, lc2, lc_total, flow1, flow2, flow1_count, flow2_count

    # Labjack write tasks
    def set_valve(self, channel, state):

        try:
            ljm.eWriteName(self.handle, channel, int(state))
        except Exception as e:
            print(f"Valve write failed: {e}")

    def close(self):
        try:
            ljm.close(self.handle)
        except:
            pass