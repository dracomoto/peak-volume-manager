"""
Peak Volume Manager - Volume Controller
Controls the Windows system master volume using pycaw / Core Audio API.
Falls back to a no-op controller on non-Windows systems.
"""

import threading
import platform
import time


class VolumeController:
    """
    Controls the system master volume on Windows.
    Provides a platform-independent interface with fallback for non-Windows.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self._base_volume = 1.0       # user's desired volume level (0.0 to 1.0)
        self._current_scalar = 1.0    # our current multiplier
        self._muted = False
        self._interface = None
        self._available = False
        self._last_log_time = 0       # throttle debug output
        self._init_audio_interface()

    def _init_audio_interface(self):
        """Initialize the Windows audio interface."""
        if platform.system() != "Windows":
            print("VolumeController: Not on Windows. Running in simulation mode.")
            self._available = False
            return

        try:
            from ctypes import cast, POINTER
            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            devices = AudioUtilities.GetSpeakers()
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._interface = cast(interface, POINTER(IAudioEndpointVolume))
            self._base_volume = self._interface.GetMasterVolumeLevelScalar()
            self._available = True
            print(f"VolumeController: Connected. Current volume: {self._base_volume:.0%}")

        except Exception as e:
            print(f"VolumeController: Could not initialize: {e}")
            self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def get_current_volume(self) -> float:
        """Get the current system volume as a scalar (0.0 to 1.0)."""
        if not self._available:
            return self._base_volume
        try:
            return self._interface.GetMasterVolumeLevelScalar()
        except Exception:
            return self._base_volume

    def capture_base_volume(self):
        """
        Capture the current system volume as the 'base' level.
        This is what the user has set manually — we reduce relative to this.
        """
        with self._lock:
            self._base_volume = self.get_current_volume()

    def set_base_volume(self, volume: float):
        """
        Set the base volume directly (0.0 to 1.0).
        This is the user's desired volume level — compression reduces relative to this.
        """
        with self._lock:
            self._base_volume = max(0.0, min(1.0, volume))
            # Apply immediately with current scalar
            self._apply_volume()

    def set_muted(self, muted: bool):
        """Mute or unmute the output."""
        with self._lock:
            self._muted = muted
            if not self._available:
                return
            try:
                self._interface.SetMute(1 if muted else 0, None)
            except Exception as e:
                print(f"VolumeController: Error setting mute: {e}")

    @property
    def muted(self) -> bool:
        if not self._available:
            return self._muted
        try:
            return bool(self._interface.GetMute())
        except Exception:
            return self._muted

    def apply_scalar(self, scalar: float):
        """
        Apply a volume scalar relative to the base volume.
        scalar=1.0 means no change, scalar=0.5 means half volume, etc.
        
        Args:
            scalar: multiplier (0.0 to 1.0+) 
        """
        with self._lock:
            self._current_scalar = scalar
            self._apply_volume()

    def _apply_volume(self):
        """Internal: set the actual system volume from base * scalar."""
        target = self._base_volume * min(self._current_scalar, 1.0)
        target = max(0.0, min(1.0, target))

        # Debug logging (throttled to once per second)
        now = time.time()
        if now - self._last_log_time > 1.0:
            if self._current_scalar < 0.99:
                print(f"  [Volume] base={self._base_volume:.0%} × scalar={self._current_scalar:.2f} → target={target:.0%}")
            self._last_log_time = now

        if not self._available:
            return

        try:
            self._interface.SetMasterVolumeLevelScalar(target, None)
        except Exception as e:
            print(f"VolumeController: Error setting volume: {e}")

    def restore(self):
        """Restore volume to the base level."""
        self.apply_scalar(1.0)

    def get_status(self) -> dict:
        """Get current volume controller status."""
        return {
            "available": self._available,
            "base_volume": self._base_volume,
            "current_scalar": self._current_scalar,
            "effective_volume": self._base_volume * min(self._current_scalar, 1.0),
            "muted": self._muted,
        }
