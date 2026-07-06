import json
import subprocess
import platform
from pathlib import Path
from pynput.keyboard import Key, Controller

keyboard = Controller()
CONFIG_PATH = Path(__file__).parent/"config.json"

class ActionDispatcher:

    def __init__(self):
        self.is_mac = platform.system() == 'Darwin'
        self._action_map = {
            "play_pause":     self.play_pause,
            "previous_track": self.previous_track,
            "next_track":     self.next_track,
            "volume_up":      self.volume_up,
            "volume_down":    self.volume_down,
            "mute":           self.mute,
            "like_song":      self.like_song,
        }

    def _load_mappings(self):
        """Read config.json every call so UI changes apply instantly"""
        with open(CONFIG_PATH) as f:
            return json.load(f)["gestures"]
    
    def dispatch(self, gesture):
        if gesture is None or gesture == 'NONE':
            return
        mappings = self._load_mappings()
        action_key = mappings.get(gesture)
        action = self._action_map.get(action_key)
        if action:
            print(f"Dispatching: {gesture} -> {action_key}")
            action()

    def _get_active_target(self):
        """Returns 'spotify', 'chrome', 'safari', or None"""
        check = lambda app: subprocess.run(
            ['osascript', '-e', 
            f'tell application "System Events" to return '
            f'(name of processes) contains "{app}"'],
            capture_output=True, text=True
        ).stdout.strip()

        if 'true' in check('Spotify'):
            return 'spotify'
        if 'true' in check('Google Chrome'):
            return 'chrome'
        if 'true' in check('Safari'):
            return 'safari'
        return None

    def _send_key_to_browser(self, key_code, modifiers=[], browser='Safari'):
        modifier_str = "using shift down" if "shift" in modifiers else ""
        script = f'''
            tell application "System Events"
                tell process "{browser}"
                    key code {key_code} {modifier_str}
                end tell
            end tell
        '''
        subprocess.run(['osascript', '-e', script], capture_output=True)

    def _system_volume(self, delta):
        self._applescript(
            f'set volume output volume '
            f'(output volume of (get volume settings) + {delta})'
        )

    def play_pause(self):
        if not self.is_mac:
            keyboard.press(Key.media_play_pause)
            keyboard.release(Key.media_play_pause)
            return
            
        target = self._get_active_target()
        if target == 'spotify':
            self._applescript('tell application "Spotify" to playpause')
        elif target == 'chrome':
            self._send_key_to_browser(49, browser='Google Chrome')
        elif target == 'safari':
            self._send_key_to_browser(49, browser='Safari')

    def next_track(self):
        if not self.is_mac:
            keyboard.press(Key.media_next)
            keyboard.release(Key.media_next)
            return

        target = self._get_active_target()
        if target == 'spotify':
            self._applescript('tell application "Spotify" to next track')
        elif target == 'chrome':
            self._send_key_to_browser(45, modifiers=["shift"], browser='Google Chrome')
        elif target == 'safari':
            self._send_key_to_browser(45, modifiers=["shift"], browser='Safari')

    def previous_track(self):
        if not self.is_mac:
            keyboard.press(Key.media_previous)
            keyboard.release(Key.media_previous)
            return

        target = self._get_active_target()
        if target == 'spotify':
            self._applescript('tell application "Spotify" to previous track')
        elif target == 'chrome':
            self._send_key_to_browser(35, modifiers=["shift"], browser='Google Chrome')
        elif target == 'safari':
            self._send_key_to_browser(35, modifiers=["shift"], browser='Safari')

    def volume_up(self):
        if self.is_mac:
            subprocess.run(['osascript', '-e', 
            'set volume output volume (output volume of (get volume settings) + 6.25)'],
            capture_output=True)
        else:
            keyboard.press(Key.media_volume_up)
            keyboard.release(Key.media_volume_up)

    def volume_down(self):
        if self.is_mac:
            subprocess.run(['osascript', '-e', 
            'set volume output volume (output volume of (get volume settings) - 6.25)'],
            capture_output=True)
        else:
            keyboard.press(Key.media_volume_down)
            keyboard.release(Key.media_volume_down)
    
    def mute(self):
        if self.is_mac:
            self._applescript('''
                set vol to output volume of (get volume settings)
                if vol > 0 then
                    set volume output volume 0
                else
                    set volume output volume 50
                end if
            ''')
        else:
            keyboard.press(Key.media_volume_mute)
            keyboard.release(Key.media_volume_mute)

    def like_song(self):
        print("PEACE — like action (customise in config UI)")

    def _applescript(self, script):
        subprocess.run(['osascript', '-e', script], capture_output=True)
