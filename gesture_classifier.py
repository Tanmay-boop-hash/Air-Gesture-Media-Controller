class GestureClassifier:

    PINCH_THRESHOLD = 0.35      # pinch_ratio below this = pinching
    POINT_ANGLE_LEFT = 160      # index_angle > this = pointing left
    POINT_ANGLE_RIGHT = 30      # index_angle < this = pointing right

    def classify(self, features):
        """
        Takes feature dict from FeatureExtractor.
        Returns a gesture label string.
        """
        if features is None:
            return 'NONE'

        thumb  = features['thumb_up']
        index  = features['index_up']
        middle = features['middle_up']
        ring   = features['ring_up']
        pinky  = features['pinky_up']
        count  = features['fingers_up']
        pinch  = features['pinch_ratio']
        angle  = features['index_angle']

        # Pinch (check first — overrides finger state logic)
        is_pinching = (pinch < self.PINCH_THRESHOLD and not middle and not ring and not pinky)
        if is_pinching:
            return 'PINCH'

        # --- Open palm ---
        if count == 5:
            return 'OPEN_PALM'

        # --- Fist ---
        if count == 0:
            return 'FIST'

        # --- Thumbs up (only thumb, all others curled) ---
        if thumb and not index and not middle and not ring and not pinky:
            return 'THUMBS_UP'

        # --- Peace (index + middle only) ---
        if index and middle and not ring and not pinky:
            return 'PEACE'

        # --- Point + directional swipe ---
        if index and not middle and not ring and not pinky:
            if angle > self.POINT_ANGLE_LEFT:
                return 'POINT_LEFT'
            elif angle < self.POINT_ANGLE_RIGHT:
                return 'POINT_RIGHT'
            else:
                return 'POINT'

        return 'NONE'