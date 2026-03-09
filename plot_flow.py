import pandas as pd
import matplotlib.pyplot as plt

# Path to CSV
# file_path = r"logs\daq_log_20260309_192147.csv"
file_path = r"logs\daq_log_20260309_203523.csv"

# Load CSV
df = pd.read_csv(file_path)

df["LC_total_kg"] *= 1e-3
df["Flow1_kgs"] *= 1e-3
df["Flow2_kgs"] *= 1e-3

# Parse timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"], format="%H:%M:%S.%f")

# Time relative to start
t0 = df["timestamp"].iloc[0]
df["t_sec"] = (df["timestamp"] - t0).dt.total_seconds()

# Flowmeter scaling
# df["Flow1_kgs"] = df["Flow1_kgs"] / 11 / 11

# ---- Smooth mass before differentiation ----
df["LC_total_smooth"] = df["LC_total_kg"].rolling(1, center=True).mean()

# Derived mass flow
df["flow_from_mass"] = -df["LC_total_smooth"].diff() / df["t_sec"].diff()

# Additional smoothing of flow signal
df["flow_from_mass"] = df["flow_from_mass"].rolling(20, center=True).mean()

# ---- Crop to steady region ----
df = df[(df["t_sec"] >= 89.5) & (df["t_sec"] <= 115)]

# Plot
fig, axs = plt.subplots(2, 1, sharex=True)

# Flowmeter reading
axs[0].plot(df["t_sec"], df["Flow1_kgs"], label="Flow metre")
axs[0].set_ylabel("Flow1 (kg/s)")
axs[0].set_title("Flow1 vs Time")
axs[0].grid(True)

# Derived flow from mass
axs[0].plot(df["t_sec"], df["flow_from_mass"], label="Derived from Mass")
axs[0].legend()


axs[1].plot(df["t_sec"], df["LC_total_kg"], label="Total", linewidth=1)
axs[1].set_ylabel("Mass (kg)")
axs[1].set_xlabel("Time (s)")
axs[1].set_title("Raw Load Cell Measurements")
axs[1].legend()
axs[1].grid(True)

plt.tight_layout()
plt.show()