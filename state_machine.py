class StateMachine:

    # frames a gesture must be stable before firing
    HOLD_FRAMES_REQUIRED = 5   
    # at 30fps this is ~0.27 seconds — feels instant, but filters out accidental flicks                           

    def __init__(self):
        self.current_gesture = 'NONE'   # currently seeing
        self.hold_count = 0             # how many consecutive frames we've seen it
        self.last_fired = 'NONE'        # what gesture last triggered an action
        self.state = 'IDLE'             # IDLE or TRIGGERED

    def update(self, raw_gesture):
        """
        Feed in the raw gesture label every frame.
        Returns the confirmed gesture to act on, or None if nothing to fire.
        """

        # --- Tracking gesture stability ---
        if raw_gesture == self.current_gesture:
            self.hold_count += 1
        else:
            # Gesture changed — reset the hold counter
            self.current_gesture = raw_gesture
            self.hold_count = 1

        # --- State: TRIGGERED ---
        # Already fired this gesture, waiting for hand to reset
        if self.state == 'TRIGGERED':
            if raw_gesture == 'NONE':
                # Hand reset — ready for next gesture
                self.state = 'IDLE'
                self.last_fired = 'NONE'
            return None     # don't fire again until reset

        # --- State: IDLE ---
        # Looking for a stable gesture to confirm
        if self.state == 'IDLE':
            if raw_gesture == 'NONE':
                return None

            if self.hold_count >= self.HOLD_FRAMES_REQUIRED:
                # Gesture confirmed — fire it and move to TRIGGERED
                self.state = 'TRIGGERED'
                self.last_fired = raw_gesture
                self.hold_count = 0
                return raw_gesture  # this is the one the dispatcher acts on

        return None

    def get_debug_info(self):
        """Useful for the OSD overlay during development."""
        return {
            'current': self.current_gesture,
            'hold': self.hold_count,
            'hold_needed': self.HOLD_FRAMES_REQUIRED,
            'state': self.state
        }