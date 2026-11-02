import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from sim import run_sim, metrics
from autotune import ziegler_nichols, genetic_algorithm

os.makedirs("results", exist_ok=True)

zn, _ = ziegler_nichols()
ga, _ = genetic_algorithm(verbose=False)

# Each stage: (title, gains)
stages = [
    ("P only: Kp=100 (stops short of the target)", (100, 0, 0)),
    ("Add I: Ki=200 (the gap closes)", (100, 200, 0)),
    ("Add a little D: Kd=5 (overshoot gone, settles sooner)", (100, 200, 5)),
    ("Ziegler-Nichols", zn),
    ("Genetic algorithm", ga),
]

runs = []
for title, g in stages:
    t, s, v = run_sim(*g, duration=2.0)
    ov, rise, settle, sse = metrics(t, s, 1.0)
    runs.append((title, g, t, s, ov, settle))

DRAW = 20      # frames spent drawing the curve
HOLD = 12      # frames spent holding the finished curve
PER = DRAW + HOLD

fig, ax = plt.subplots(figsize=(6, 3.6), dpi=80)
ax.axhline(1.0, color="gray", linestyle="--", label="Target")
ax.axhspan(0.98, 1.02, color="green", alpha=0.12)
ax.set_xlim(0, 2)
ax.set_ylim(0, 1.15)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Speed (rad/s)")
ax.grid(alpha=0.3)
(line,) = ax.plot([], [], linewidth=2.5, color="tab:blue")
title = ax.set_title("")
info = ax.text(0.98, 0.08, "", transform=ax.transAxes, ha="right", fontsize=9,
               bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))
fig.subplots_adjust(left=0.11, right=0.97, bottom=0.17, top=0.86)


def animate(frame):
    stage, k = divmod(frame, PER)
    name, g, t, s, ov, settle = runs[stage]
    upto = len(t) if k >= DRAW else int(len(t) * (k + 1) / DRAW)
    line.set_data(t[:upto], s[:upto])
    title.set_text(name)
    if k >= DRAW:
        settle_txt = "never" if np.isnan(settle) else f"{settle:.2f} s"
        info.set_text(f"Kp={g[0]:.0f} Ki={g[1]:.0f} Kd={g[2]:.0f}\n"
                      f"overshoot {ov:.1f}%   settling {settle_txt}")
    else:
        info.set_text("")
    return line, title, info


anim = FuncAnimation(fig, animate, frames=len(runs) * PER, blit=False)
anim.save("results/demo.gif", writer=PillowWriter(fps=12))
print("Saved results/demo.gif")