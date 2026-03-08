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

        # Convert
        pt1 = (pt1_v - system_config.PT_OFFSET)*system_config.PT_SCALE
        pt2 = (pt1_v - system_config.PT_OFFSET)*system_config.PT_SCALE

        lc1 = (lc1_v - system_config.LC_OFFSET)*system_config.LC_SCALE
        lc2 = (lc2_v - system_config.LC_OFFSET)*system_config.LC_SCALE
        
        return pt1, pt2, lc1, lc2, flow