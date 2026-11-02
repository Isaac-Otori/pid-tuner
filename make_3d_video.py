import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from sim import run_sim, metrics
from autotune import ziegler_nichols, genetic_algorithm

os.makedirs("results", exist_ok=True)

# ----------------------------------------------------------------- settings
STAGE_SECONDS = 3.0      # simulated seconds per stage
FPS = 20
VISUAL_SPEED = 6.0       # shaft drawn 6x faster than real, so you can see it
SETPOINT = 1.0
DT = 0.001

zn, _ = ziegler_nichols()
ga, _ = genetic_algorithm(verbose=False)

stages = [
    ("P only", (100, 0, 0)),
    ("P + I", (100, 200, 0)),
    ("P + I + a little D", (100, 200, 5)),
    ("Ziegler-Nichols", zn),
    ("Genetic algorithm", ga),
]

# ----------------------------------------------------------------- simulate every stage
runs = []
for name, g in stages:
    t, speed, volts = run_sim(*g, setpoint=SETPOINT, duration=STAGE_SECONDS, dt=DT)
    angle = np.cumsum(speed) * DT * VISUAL_SPEED       # shaft angle = integral of speed
    ov, rise, settle, sse = metrics(t, speed, SETPOINT)
    runs.append(dict(name=name, g=g, t=t, speed=speed, volts=volts,
                     angle=angle, ov=ov, settle=settle))

STEP = int(round(1.0 / (FPS * DT)))          # simulation samples per video frame
FRAMES_PER_STAGE = len(runs[0]["t"]) // STEP
TOTAL = FRAMES_PER_STAGE * len(runs)


# ----------------------------------------------------------------- 3D drawing helpers
def cylinder(ax, x0, x1, r, color, alpha=1.0):
    th = np.linspace(0, 2 * np.pi, 40)
    x = np.array([x0, x1])
    X, TH = np.meshgrid(x, th)
    ax.plot_surface(X, r * np.cos(TH), r * np.sin(TH), color=color,
                    alpha=alpha, linewidth=0, shade=True)


def disc_sector(ax, x, r, a0, a1, color):
    th = np.linspace(a0, a1, 12)
    pts = [(x, 0, 0)] + [(x, r * np.cos(a), r * np.sin(a)) for a in th]
    ax.add_collection3d(Poly3DCollection([pts], facecolor=color,
                                         edgecolor="k", linewidth=0.4))


def draw_motor(ax, angle, speed_frac):
    ax.cla()
    ax.set_axis_off()
    ax.set_xlim(-2.2, 2.2)
    ax.set_ylim(-1.6, 1.6)
    ax.set_zlim(-1.6, 1.6)
    ax.set_box_aspect((4.4, 3.2, 3.2))
    ax.view_init(elev=18, azim=-62)

    cylinder(ax, -2.0, 0.0, 1.0, "#6b7280")              # motor body
    cylinder(ax, 0.0, 1.4, 0.14, "#d1d5db")              # shaft
    # a stripe along the shaft so its rotation is visible
    ax.plot([0.0, 1.4], [0.15 * np.cos(angle)] * 2, [0.15 * np.sin(angle)] * 2,
            color="#111827", linewidth=2.5)
    # colour wheel (four sectors) on the end of the shaft
    cols = ["#ef4444", "#3b82f6", "#ef4444", "#3b82f6"]
    for k in range(4):
        a0 = angle + k * np.pi / 2
        disc_sector(ax, 1.45, 0.95, a0, a0 + np.pi / 2, cols[k])
    ax.text(-1.0, 0, 1.25, "DC motor", ha="center", fontsize=10, color="#374151")


# ----------------------------------------------------------------- figure
fig = plt.figure(figsize=(11, 5.6), dpi=90)
ax3d = fig.add_axes([0.01, 0.05, 0.50, 0.85], projection="3d")
axS = fig.add_axes([0.58, 0.55, 0.39, 0.33])
axV = fig.add_axes([0.58, 0.12, 0.39, 0.30])
head = fig.text(0.5, 0.95, "", ha="center", fontsize=14, weight="bold")
info = fig.text(0.58, 0.01, "", fontsize=10, family="monospace")
note = fig.text(0.02, 0.01, f"Shaft rotation drawn at {VISUAL_SPEED:.0f}x real speed",
                fontsize=8, color="gray")


def draw_frame(frame):
    s_idx, k = divmod(frame, FRAMES_PER_STAGE)
    r = runs[s_idx]
    n = min((k + 1) * STEP, len(r["t"]))
    t, speed, volts = r["t"][:n], r["speed"][:n], r["volts"][:n]

    draw_motor(ax3d, r["angle"][n - 1], speed[-1] / SETPOINT)

    axS.cla()
    axS.axhline(SETPOINT, color="gray", linestyle="--", linewidth=1)
    axS.axhspan(SETPOINT * 0.98, SETPOINT * 1.02, color="green", alpha=0.12)
    axS.plot(t, speed, color="tab:blue", linewidth=2)
    axS.set_xlim(0, STAGE_SECONDS)
    axS.set_ylim(0, 1.25)
    axS.set_ylabel("Speed (rad/s)")
    axS.grid(alpha=0.3)

    axV.cla()
    axV.plot(t, volts, color="tab:orange", linewidth=1.5)
    axV.axhline(24, color="gray", linestyle=":")
    axV.set_xlim(0, STAGE_SECONDS)
    axV.set_ylim(-26, 27)
    axV.set_xlabel("Time (s)")
    axV.set_ylabel("Voltage (V)")
    axV.grid(alpha=0.3)

    g = r["g"]
    head.set_text(f"{r['name']}   (Kp={g[0]:.0f}, Ki={g[1]:.0f}, Kd={g[2]:.0f})")
    if k > FRAMES_PER_STAGE - 8:     # show the stage result at the end
        st = "never" if np.isnan(r["settle"]) else f"{r['settle']:.2f} s"
        info.set_text(f"overshoot {r['ov']:.1f}%   settling {st}")
    else:
        info.set_text("")


# ----------------------------------------------------------------- render
if __name__ == "__main__":
    from matplotlib.animation import FuncAnimation, FFMpegWriter

    import imageio_ffmpeg
    matplotlib.rcParams["animation.ffmpeg_path"] = imageio_ffmpeg.get_ffmpeg_exe()

    anim = FuncAnimation(fig, draw_frame, frames=TOTAL)
    anim.save("results/motor_3d.mp4", writer=FFMpegWriter(fps=FPS, bitrate=1800))
    print("Saved results/motor_3d.mp4")