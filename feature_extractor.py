import math

class FeatureExtractor:

    # Landmark index constants — use these by name, never magic numbers
    WRIST = 0
    THUMB_TIP = 4
    INDEX_MCP = 5   # base knuckle of index finger
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_TIP = 12
    RING_MCP = 13
    RING_TIP = 16
    PINKY_MCP = 17
    PINKY_TIP = 20

    def extract(self, landmarks):
        """
        Takes the 21 (x, y, z) landmark tuples from HandTracker.
        Returns a feature dict describing the hand shape.
        """
        if landmarks is None:
            return None

        features = {}

        # --- Hand size ruler ---
        # Distance from wrist to middle finger MCP (base knuckle)
        # Everything gets normalized by this so scale doesn't matter
        hand_size = self._distance(landmarks[self.WRIST], landmarks[self.MIDDLE_MCP])
        if hand_size < 1:
            return None  # degenerate case, hand too close or detection glitch

        # --- Finger extension (True = extended/up, False = curled/down) ---
        features['thumb_up']  = self._is_thumb_extended(landmarks)
        features['index_up']  = self._is_finger_extended(landmarks, self.INDEX_MCP,  self.INDEX_TIP)
        features['middle_up'] = self._is_finger_extended(landmarks, self.MIDDLE_MCP, self.MIDDLE_TIP)
        features['ring_up']   = self._is_finger_extended(landmarks, self.RING_MCP,   self.RING_TIP)
        features['pinky_up']  = self._is_finger_extended(landmarks, self.PINKY_MCP,  self.PINKY_TIP)

        # Count of extended fingers (0-5)
        features['fingers_up'] = sum([
            features['thumb_up'],
            features['index_up'],
            features['middle_up'],
            features['ring_up'],
            features['pinky_up']
        ])

        # --- Pinch distance (normalized) ---
        # How close is thumb tip to index tip?
        # Small value = pinching, large value = open
        raw_pinch = self._distance(landmarks[self.THUMB_TIP], landmarks[self.INDEX_TIP])
        features['pinch_ratio'] = raw_pinch / hand_size

        # --- Index finger direction ---
        # Vector from index MCP to index tip — tells us which way finger is pointing
        dx = landmarks[self.INDEX_TIP][0] - landmarks[self.INDEX_MCP][0]
        dy = landmarks[self.INDEX_TIP][1] - landmarks[self.INDEX_MCP][1]
        features['index_angle'] = math.degrees(math.atan2(-dy, dx))  # -dy because y is flipped in image coords

        return features

    def _distance(self, p1, p2):
        return math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2)

    def _is_finger_extended(self, landmarks, mcp_idx, tip_idx):
        """
        A finger is extended if its tip is meaningfully above its MCP joint.
        'Above' in image coords means smaller y value.
        We add a small threshold to avoid flickering on borderline cases.
        """
        tip_y = landmarks[tip_idx][1]
        mcp_y = landmarks[mcp_idx][1]
        return tip_y < mcp_y - 20  # 20px threshold prevents jitter

    def _is_thumb_extended(self, landmarks):
        """
        Thumb is special — it extends sideways not upward.
        We compare thumb tip x to the index MCP x instead.
        (Works for right hand facing camera — mirrored frame)
        """
        thumb_tip_x = landmarks[self.THUMB_TIP][0]
        index_mcp_x = landmarks[self.INDEX_MCP][0]
        return thumb_tip_x < index_mcp_x - 20  # thumb is to the left of index base