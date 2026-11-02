import numpy as np
import matplotlib.pyplot as plt
import streamlit as st

from sim import run_sim, metrics
from autotune import ziegler_nichols, genetic_algorithm

st.set_page_config(page_title="PID Tuner", layout="wide")
st.title("PID Tuner: DC Motor Speed Control")
st.write(
    "Move the sliders to change the controller gains and watch the "
    "simulated motor respond. The goal: reach the target fast, with little "
    "overshoot, and settle quickly."
)

# ---------- Auto-tune helpers ----------
def snap(value, step, lo, hi):
    """Round to the slider's step and keep inside its range."""
    return float(min(hi, max(lo, round(value / step) * step)))


def set_gains(kp, ki, kd):
    st.session_state["kp"] = snap(kp, 5.0, 0.0, 1000.0)
    st.session_state["ki"] = snap(ki, 10.0, 0.0, 5000.0)
    st.session_state["kd"] = snap(kd, 1.0, 0.0, 100.0)


def use_zn():
    gains, _ = ziegler_nichols()
    set_gains(*gains)


def use_ga():
    gains, _ = genetic_algorithm(verbose=False)
    set_gains(*gains)


# ---------- Sidebar controls ----------
# Starting values (only used the first time the page loads)
st.session_state.setdefault("kp", 100.0)
st.session_state.setdefault("ki", 200.0)
st.session_state.setdefault("kd", 0.0)

st.sidebar.header("Controller gains")
kp = st.sidebar.slider("Kp (proportional)", 0.0, 1000.0, step=5.0, key="kp")
ki = st.sidebar.slider("Ki (integral)", 0.0, 5000.0, step=10.0, key="ki")
kd = st.sidebar.slider("Kd (derivative)", 0.0, 100.0, step=1.0, key="kd")

st.sidebar.header("Auto-tune")
st.sidebar.button("Ziegler-Nichols", on_click=use_zn)
st.sidebar.button("Genetic algorithm (takes a few seconds)", on_click=use_ga)

st.sidebar.header("Simulation")
setpoint = st.sidebar.slider("Target speed (rad/s)", 0.5, 5.0, 1.0, step=0.1)
duration = st.sidebar.slider("Duration (s)", 2.0, 10.0, 5.0, step=0.5)

# ---------- Run the simulation ----------
t, speed, volts = run_sim(kp, ki, kd, setpoint=setpoint, duration=duration)
overshoot, rise, settling, sse = metrics(t, speed, setpoint)


def fmt(value, unit, decimals=3):
    return "never" if np.isnan(value) else f"{value:.{decimals}f} {unit}"


# ---------- Metric cards ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Overshoot", f"{overshoot:.1f} %")
c2.metric("Rise time (10-90%)", fmt(rise, "s"))
c3.metric("Settling time (2%)", fmt(settling, "s"))
c4.metric("Steady-state error", f"{sse:.3f} rad/s")

# ---------- Plots ----------
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)

ax1.plot(t, speed, linewidth=2, label="Motor speed")
ax1.axhline(setpoint, color="red", linestyle="--", label="Target")
ax1.axhspan(setpoint * 0.98, setpoint * 1.02, color="green", alpha=0.12,
            label="±2% band")
ax1.set_ylabel("Speed (rad/s)")
ax1.set_title("Step response")
ax1.legend(loc="lower right")
ax1.grid(alpha=0.3)

ax2.plot(t, volts, color="orange", linewidth=1.5)
ax2.axhline(24, color="gray", linestyle=":", label="Voltage limit (±24 V)")
ax2.axhline(-24, color="gray", linestyle=":")
ax2.set_xlabel("Time (s)")
ax2.set_ylabel("Control voltage (V)")
ax2.set_title("Controller output")
ax2.legend(loc="upper right")
ax2.grid(alpha=0.3)

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ---------- Help text ----------
with st.expander("What do Kp, Ki and Kd do?"):
    st.markdown(
        "- **Kp** reacts to the current error. Higher means faster, but "
        "P-only leaves a permanent gap.\n"
        "- **Ki** adds up past error to remove that gap. Too much causes "
        "overshoot.\n"
        "- **Kd** reacts to how fast the speed is changing. It damps "
        "overshoot."
    )