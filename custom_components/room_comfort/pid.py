"""Bounded PID demand with a temperature deadband and output hysteresis."""

from math import isfinite


class RoomPID:
    """Demand is 0..1, never a claim about physical valve position.

    Time constants use minutes. Derivative acts on measurement to avoid target
    kicks; anti-windup rejects integral growth further into saturation. Inside
    the deadband, integration freezes and proportional noise is suppressed.
    """

    def __init__(self, kp=.3, ki=.006, kd=.1, deadband=.1, output_step=.03, bias=.4):
        self.kp, self.ki, self.kd = kp, ki, kd
        self.deadband, self.output_step = deadband, output_step
        self.bias = bias
        self.reset()

    def reset(self):
        self.integral = 0.0
        self.output = 0.0
        self._time = None
        self._temperature = None
        self._derivative = 0.0

    def update(self, temperature, target, now):
        if not all(isfinite(v) for v in (temperature, target, now)):
            self.reset()
            return 0.0
        error = target - temperature
        if self._time is None:
            self._time, self._temperature = now, temperature
            self.output = max(0.0, min(1.0, self.bias + self.kp * error))
            return self.output
        dt = max(0.0, now - self._time) / 60
        if dt < .25:
            return self.output
        # Do not integrate an entire downtime or long sensor outage.
        dt = min(dt, 2.0)
        derivative = (temperature - self._temperature) / dt
        alpha = dt / (2.0 + dt)
        self._derivative += alpha * (derivative - self._derivative)
        self._time, self._temperature = now, temperature
        # Freeze I and suppress proportional noise in-band, but still return
        # towards holding demand. Never latch a full warm-up output at target.
        effective_error = 0.0 if abs(error) <= self.deadband else error
        integral = max(-1.0, min(1.0, self.integral + self.ki * effective_error * dt))
        candidate = self.bias + self.kp * effective_error + integral - self.kd * self._derivative
        if not (candidate > 1 and error > 0 or candidate < 0 and error < 0):
            self.integral = integral
        wanted = max(0.0, min(1.0, self.bias + self.kp * effective_error + self.integral - self.kd * self._derivative))
        # Reduce warm-up demand faster than increasing it near the target.
        wanted = max(self.output - .35 * dt, min(self.output + .15 * dt, wanted))
        if abs(wanted - self.output) >= self.output_step or wanted in (0.0, 1.0):
            self.output = wanted
        return self.output


def trv_target(local_temperature, output, minimum, maximum, step=.5):
    """Trim the native TRV target around its own reported temperature.

    No full-open/full-off PWM. At zero demand the head idles below its local
    reading; at full demand the offset is bounded to +3°C, not max_temp.
    """
    output = max(0.0, min(1.0, output))
    target = local_temperature - 2.0 + 5.0 * output
    step = step if step and step > 0 else .5
    return max(minimum, min(maximum, round(target / step) * step))
