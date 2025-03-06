import numpy as np
import matplotlib.pyplot as plt

# Simulating time steps
time = np.arange(0, 20, 1)

# 1️⃣ Open-Loop vs. Closed-Loop Power Control
open_loop_power = np.full_like(time, -10)  # Static power level
closed_loop_power = -10 + np.sin(time / 2) * 3  # Adjusting power dynamically

plt.figure(figsize=(10, 5))
plt.plot(time, open_loop_power, 'r--', label="Open-Loop Power")
plt.plot(time, closed_loop_power, 'b-', label="Closed-Loop Power")
plt.xlabel("Time (Transmission Occasions)")
plt.ylabel("UE Transmit Power (dBm)")
plt.title("1️⃣ Open-Loop vs. Closed-Loop Power Control")
plt.legend()
plt.grid(True)
plt.show()


# 2️⃣ Closed-Loop Power Control Process (TPC Adjustments)
power_levels = [-10, -9, -7, -8, -6, -7, -5, -6, -4, -5]  # Simulated UE power adjustments
time_steps = np.arange(len(power_levels))

plt.figure(figsize=(10, 5))
plt.step(time_steps, power_levels, 'g-', where="mid", label="UE Power Adjustment")
plt.xlabel("Time Steps (TPC Commands)")
plt.ylabel("UE Transmit Power (dBm)")
plt.title("2️⃣ Closed-Loop Power Control Adjustments")
plt.legend()
plt.grid(True)
plt.show()


# 3️⃣ SINR vs. Power Adjustment
power_values = np.linspace(-20, 23, 20)
sinr_values = 5 + np.log2(1 + (power_values + 25) / 10) * 10  # SINR model

plt.figure(figsize=(10, 5))
plt.plot(power_values, sinr_values, 'm-', label="SINR vs Power")
plt.xlabel("UE Transmit Power (dBm)")
plt.ylabel("SINR (dB)")
plt.title("3️⃣ SINR vs. Power Adjustment")
plt.legend()
plt.grid(True)
plt.show()


# 4️⃣ Throughput vs. Power (With & Without CLPC)
throughput_without_clpc = np.minimum(10 * np.log2(1 + (power_values + 30) / 10), 100)
throughput_with_clpc = np.minimum(10 * np.log2(1 + (power_values + 25) / 10), 110)

plt.figure(figsize=(10, 5))
plt.plot(power_values, throughput_without_clpc, 'r--', label="Without CLPC")
plt.plot(power_values, throughput_with_clpc, 'b-', label="With CLPC")
plt.xlabel("UE Transmit Power (dBm)")
plt.ylabel("Throughput (Mbps)")
plt.title("4️⃣ Throughput vs. Power (With vs Without CLPC)")
plt.legend()
plt.grid(True)
plt.show()