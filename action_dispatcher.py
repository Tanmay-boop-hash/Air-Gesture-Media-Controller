import subprocess
import platform
from pynput.keyboard import Key, Controller

keyboard = Controller()

class ActionDispatcher:

    def __init__(self):
        self.is_mac = platform.system() == 'Darwin'

    def dispatch(self, gesture):
        if gesture is None or gesture == 'NONE':
            return
        actions = {
            'OPEN_PALM':   self.play_pause,
            'FIST':        self.mute,
            'POINT_LEFT':  self.previous_track,
            'POINT_RIGHT': self.next_track,
            'THUMBS_UP':   self.volume_up,
            'PINCH':       self.volume_down,
            'PEACE':       self.like_song,
        }
        action = actions.get(gesture)
        if action:
            print(f"Dispatching: {gesture}")
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
        