PT1 = "AIN0"
PT2 = "AIN6"

# Straight LJ, no tickinamp
#LC1 = "AIN0" # -ve, AIN1 +ve
#LC2 = "AIN2" # -ve, AIN3 +ve

# LJ tickinamp 11x
LC1 = "AIN10" # Tank 1
LC2 = "AIN11" # Tank 2

LC3 = "AIN12" # Thrust 1
LC4 = "AIN13" # Thrust 2

FLOW1 = "DIO0_EF_READ_A_F"
FLOW2 = "DIO1_EF_READ_A_F"


SAMPLE_RATE = 100
DATA_FOLDER = "data/test_runs"

# CSV Headers
headers = [
    "PT1_bar",
    "PT2_bar",
    "LC_tank_g",
    "LC_thrust_g",
    "Flow1_gs",
    "Flow2_gs"
]
