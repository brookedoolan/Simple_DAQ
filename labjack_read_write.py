from labjack import ljm
import system_config

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
            # Configure differential load cell channel
            ljm.eWriteName(self.handle, "AIN2_NEGATIVE_CH", 3)
            ljm.eWriteName(self.handle, "AIN4_NEGATIVE_CH", 5)
            # Small range for better resolution
            ljm.eWriteName(self.handle, "AIN2_RANGE", 0.1) # +/- 0.1V
            ljm.eWriteName(self.handle, "AIN4_RANGE", 0.1)

            # Higher resolution
            ljm.eWriteName(self.handle, "AIN_ALL_RESOLUTION_INDEX", 8) 
            # Stream safe settling time 
            ljm.eWriteName(self.handle, "AIN_ALL_SETTLING_US", 50) 

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

            return pt1, pt2, lc1, lc2, flow1, flow2

        values = ljm.eReadNames(self.handle, len(self.names), self.names)
        pt1_v, pt2_v, lc1_v, lc2_v, flow1, flow2 = values

        # Convert readings. Gauge -> absolute readings
        P_atm = 1.013 # atmospheric pressure in bar
        # CURRENTLY FOR 500 PSI SENSOR
        pt1 = ((pt1_v - 0.5)*150/4)*0.06895 + P_atm # psi to bar
        pt2 = ((pt2_v - 0.5)*500/4)*0.06895 + P_atm

        # CALIBRATE
        lc1 = (lc1_v - 0.1)*200
        lc2 = (lc2_v - 0.1)*200
        
        # CALIBRATE 
        flow1 = flow1
        flow2 = flow2
        
        return pt1, pt2, lc1, lc2, flow1, flow2

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