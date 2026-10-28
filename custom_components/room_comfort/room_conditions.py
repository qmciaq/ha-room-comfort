"""Window debounce and conservative room occupancy timers, without HA I/O."""


class RoomConditions:
    def __init__(self):
        self.open_since = {}
        self.absent_since = None
        self.occupied = None
        self.next_check = None
        self.window_pending = False

    def evaluate(self, *, windows, presence, now, mode, window_delay,
                 pause_heat, pause_cool, heat_minutes, cool_minutes):
        deadlines = []
        self.window_pending = False
        window_blocked = False
        for entity_id in list(self.open_since):
            if windows.get(entity_id) != "on":
                self.open_since.pop(entity_id)
        for entity_id, value in windows.items():
            if value not in ("on", "off"):
                window_blocked = True  # Unknown window state cannot prove closed.
            elif value == "on":
                opened = self.open_since.setdefault(entity_id, now)
                deadline = opened + window_delay
                if now >= deadline:
                    window_blocked = True
                else:
                    deadlines.append(deadline)
                    self.window_pending = True
        values = list(presence.values())
        self.occupied = True if "on" in values else False if values and all(v == "off" for v in values) else None
        if self.occupied is False:
            if self.absent_since is None:
                self.absent_since = now
        else:
            # Unknown presence preserves comfort and resets the absence timer.
            self.absent_since = None
        empty_blocked = False
        pause = (mode == "heat" and pause_heat) or (mode == "cool" and pause_cool)
        if pause and self.absent_since is not None:
            delay = heat_minutes if mode == "heat" else cool_minutes
            deadline = self.absent_since + delay * 60
            if now >= deadline:
                empty_blocked = True
            else:
                deadlines.append(deadline)
        self.next_check = min(deadlines) if deadlines else None
        return "window_open" if window_blocked else "room_unoccupied" if empty_blocked else None
