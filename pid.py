class PID:
    """PID controller with output limits and anti-windup."""

    def __init__(self, kp, ki, kd, out_min=-24.0, out_max=24.0):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.out_min, self.out_max = out_min, out_max
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.prev_measurement = None

    def update(self, setpoint, measurement, dt):
        error = setpoint - measurement

        # Derivative on the measurement (avoids a spike when the setpoint jumps)
        if self.prev_measurement is None:
            derivative = 0.0
        else:
            derivative = -(measurement - self.prev_measurement) / dt
        self.prev_measurement = measurement

        # Candidate output
        candidate_integral = self.integral + error * dt
        output = (self.kp * error
                  + self.ki * candidate_integral
                  + self.kd * derivative)

        # Anti-windup: only keep integrating if we are not saturated
        if self.out_min <= output <= self.out_max:
            self.integral = candidate_integral
        output = max(self.out_min, min(self.out_max, output))
        return output