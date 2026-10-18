class DCMotor:
    """DC motor model. Input = voltage (V), output = shaft speed (rad/s).

    Electrical:  L * di/dt = V - R*i - Ke*omega
    Mechanical:  J * domega/dt = Kt*i - b*omega
    """

    def __init__(self, J=0.01, b=0.1, K=0.01, R=1.0, L=0.5):
        self.J, self.b, self.K, self.R, self.L = J, b, K, R, L
        self.reset()

    def reset(self):
        self.omega = 0.0   # speed (rad/s)
        self.i = 0.0       # current (A)

    def step(self, voltage, dt):
        di = (voltage - self.R * self.i - self.K * self.omega) / self.L
        domega = (self.K * self.i - self.b * self.omega) / self.J
        self.i += di * dt
        self.omega += domega * dt
        return self.omega