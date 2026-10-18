import numpy as np
from motor import DCMotor
from pid import PID


def run_sim(kp, ki, kd, setpoint=1.0, duration=5.0, dt=0.001):
    motor = DCMotor()
    pid = PID(kp, ki, kd)
    n = int(duration / dt)
    t = np.arange(n) * dt
    speed = np.zeros(n)
    volts = np.zeros(n)
    for k in range(n):
        v = pid.update(setpoint, motor.omega, dt)
        speed[k] = motor.step(v, dt)
        volts[k] = v
    return t, speed, volts


def metrics(t, speed, setpoint):
    peak = speed.max()
    overshoot = max(0.0, (peak - setpoint) / setpoint * 100)

    above10 = np.where(speed >= 0.1 * setpoint)[0]
    above90 = np.where(speed >= 0.9 * setpoint)[0]
    rise = (t[above90[0]] - t[above10[0]]) if len(above90) and len(above10) else float("nan")

    outside = np.where(np.abs(speed - setpoint) > 0.02 * setpoint)[0]
    if len(outside) == 0:
        settling = 0.0
    elif outside[-1] >= len(t) - 1:
        settling = float("nan")   # never settles
    else:
        settling = t[outside[-1] + 1]

    sse = abs(setpoint - speed[-1])
    return overshoot, rise, settling, sse


if __name__ == "__main__":
    print("(Kp, Ki, Kd) -> overshoot %, rise s, settling s, steady-state error")
    for gains in [(1, 0, 0), (100, 0, 0), (100, 200, 0),
                  (100, 200, 10), (100, 1000, 0), (300, 3000, 20)]:
        t, s, v = run_sim(*gains)
        print(gains, ["%.3f" % m for m in metrics(t, s, 1.0)])