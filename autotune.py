import numpy as np
from motor import DCMotor
from sim import run_sim, metrics

DT = 0.001
BOUNDS = np.array([[0.0, 1000.0],    # Kp
                   [0.0, 5000.0],    # Ki
                   [0.0, 100.0]])    # Kd


# ---------------------------------------------------------------- Ziegler-Nichols
def ziegler_nichols(voltage=1.0, duration=5.0):
    """Reaction-curve Ziegler-Nichols PID tuning.

    1. Apply a constant voltage to the motor with NO controller (open loop).
    2. Find the steepest point of the speed curve and draw a tangent there.
    3. Read three numbers: K (gain), L (delay) and T (time constant).
    4. Plug them into the Ziegler-Nichols formulas.
    """
    motor = DCMotor()
    n = int(duration / DT)
    t = np.arange(n) * DT
    y = np.array([motor.step(voltage, DT) for _ in range(n)])

    final = y[-1]
    K = final / voltage                      # speed gained per volt
    slope = np.gradient(y, DT)
    i = int(np.argmax(slope))                # steepest point
    L = t[i] - y[i] / slope[i]               # where the tangent hits zero
    T = final / slope[i]                     # how long the tangent takes to reach the final value

    kp = 1.2 * T / (K * L)
    ti = 2.0 * L
    td = 0.5 * L
    return (kp, kp / ti, kp * td), (K, L, T)


# ---------------------------------------------------------------- Genetic algorithm
def cost(gains, setpoint=1.0, duration=3.0):
    """Lower is better. Mixes the things we care about into one number."""
    t, speed, _ = run_sim(*gains, setpoint=setpoint, duration=duration, dt=DT)
    overshoot, rise, settling, sse = metrics(t, speed, setpoint)
    if np.isnan(settling):
        settling = duration * 2          # heavy penalty: never settled
    return settling + 0.1 * overshoot + 10.0 * sse


def genetic_algorithm(pop_size=40, generations=30, seed=1, verbose=True):
    rng = np.random.default_rng(seed)
    lo, hi = BOUNDS[:, 0], BOUNDS[:, 1]
    span = hi - lo

    pop = lo + rng.random((pop_size, 3)) * span          # random start
    history = []

    for gen in range(generations):
        scores = np.array([cost(g) for g in pop])
        order = np.argsort(scores)
        pop, scores = pop[order], scores[order]
        history.append(scores[0])
        if verbose:
            print(f"gen {gen + 1:2d}  best cost {scores[0]:.3f}  "
                  f"gains Kp={pop[0][0]:.1f} Ki={pop[0][1]:.1f} Kd={pop[0][2]:.1f}")

        # next generation: keep the 4 best unchanged ("elitism")
        new_pop = [pop[i].copy() for i in range(4)]
        while len(new_pop) < pop_size:
            # tournament selection: pick 3 random, the best one becomes a parent
            def pick():
                idx = rng.integers(0, pop_size, 3)
                return pop[idx[np.argmin(scores[idx])]]
            p1, p2 = pick(), pick()

            # crossover: blend the two parents
            w = rng.random(3)
            child = w * p1 + (1 - w) * p2

            # mutation: small random nudges
            mutate = rng.random(3) < 0.3
            child = child + mutate * rng.normal(0, 0.05, 3) * span
            new_pop.append(np.clip(child, lo, hi))
        pop = np.array(new_pop)

    scores = np.array([cost(g) for g in pop])
    best = pop[int(np.argmin(scores))]
    return tuple(best), history


if __name__ == "__main__":
    zn, (K, L, T) = ziegler_nichols()
    print("ZN: K=%.4f L=%.4f T=%.4f" % (K, L, T), "gains", [round(float(g), 2) for g in zn])
    ga, hist = genetic_algorithm()
    print("GA gains", [round(float(g), 2) for g in ga])