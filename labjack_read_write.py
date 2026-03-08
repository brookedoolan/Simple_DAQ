from labjack import ljm
import system_config

class DAQ:

    def __init__(self):
        self.handle = ljm.openS("T7", "USB", "ANY")

    def read_sensors(self):

        pt1_v = ljm.eReadName(self.handle, system_config.PT1)
        pt2_v = ljm.eReadName(self.handle, system_config.PT2)

        lc1_v = ljm.eReadName(self.handle, system_config.LC1)
        lc2_v = ljm.eReadName(self.handle, system_config.PT2)

        flow = ljm.eReadName(self.handle, system_config.FLOW)

        # Convert readings. Gauge -> absolute readings
        P_atm = 1.013 # atmospheric pressure in bar
        pt1 = ((pt1_v - 0.5)*500/4)*0.06895 + P_atm # psi to bar
        pt2 = ((pt2_v - 0.5)*500/4)*0.06895 + P_atm

        lc1 = (lc1_v - system_config.LC_OFFSET)*system_config.LC_SCALE
        lc2 = (lc2_v - system_config.LC_OFFSET)*system_config.LC_SCALE
        
        return pt1, pt2, lc1, lc2, flow