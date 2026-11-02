import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sim import run_sim, metrics
from autotune import ziegler_nichols, genetic_algorithm

os.makedirs("results", exist_ok=True)

# >>> Put YOUR best manual gains from the Step 3 challenge here <<<
MANUAL = (100, 200, 10)

zn_gains, (K, L, T) = ziegler_nichols()
ga_gains, history = genetic_algorithm(verbose=False)

methods = {
    "Manual": MANUAL,
    "Ziegler-Nichols": zn_gains,
    "Genetic algorithm": ga_gains,
}

# ---------- Table ----------
header = "| Method | Kp | Ki | Kd | Overshoot (%) | Rise (s) | Settling (s) | SS error |"
print(header)
print("|---|---|---|---|---|---|---|---|")
curves = {}
for name, g in methods.items():
    t, s, v = run_sim(*g)
    ov, rise, settle, sse = metrics(t, s, 1.0)
    curves[name] = (t, s)
    print(f"| {name} | {g[0]:.1f} | {g[1]:.1f} | {g[2]:.1f} | "
          f"{ov:.2f} | {rise:.3f} | {settle:.3f} | {sse:.4f} |")

# ---------- Plot 1: step responses ----------
plt.figure(figsize=(9, 5))
for name, (t, s) in curves.items():
    plt.plot(t, s, linewidth=2, label=name)
plt.axhline(1.0, color="gray", linestyle="--", label="Target")
plt.xlim(0, 2)
plt.xlabel("Time (s)")
plt.ylabel("Speed (rad/s)")
plt.title("Tuning methods compared")
plt.legend()
plt.grid(alpha=0.3)
plt.savefig("results/comparison.png", dpi=150, bbox_inches="tight")
plt.close()

# ---------- Plot 2: GA convergence ----------
plt.figure(figsize=(7, 4))
plt.plot(range(1, len(history) + 1), history, "o-")
plt.xlabel("Generation")
plt.ylabel("Best cost (lower is better)")
plt.title("Genetic algorithm convergence")
plt.grid(alpha=0.3)
plt.savefig("results/ga_convergence.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved results/comparison.png and results/ga_convergence.png")