"""
Peak Volume Manager - Audio Monitor
Captures system audio via WASAPI loopback (Windows) or default input,
analyzes levels, and emits results for the GUI and volume controller.
"""

import threading
import time
import numpy as np

try:
    import sounddevice as sd
except Exception:
    sd = None

from compressor import Compressor


class AudioMonitor:
    """
    Monitors system audio output in real-time using WASAPI loopback.
    Runs on a background thread and calls a callback with level/compression data.
    """

    def __init__(self, callback=None, block_duration_ms: int = 50):
        """
        Args:
            callback: function(result_dict) called with compressor output each block
            block_duration_ms: how often to analyze (smaller = more responsive, more CPU)
        """
        self.callback = callback
        self.block_duration_ms = block_duration_ms
        self.compressor = Compressor()
        self._running = False
        self._thread = None
        self._stream = None
        self._enabled = True
        self._lock = threading.Lock()

        # Buffer for accumulating audio between callbacks
        self._buffer = np.array([], dtype=np.float32)
        self._sample_rate = 44100

    def find_loopback_device(self):
        """
        Find the WASAPI loopback device for system audio capture.
        On Windows, this captures what's playing through speakers/headphones.
        Returns device index or None.
        """
        if sd is None:
            return None

        try:
            devices = sd.query_devices()
            # Look for WASAPI loopback devices
            for i, dev in enumerate(devices):
                name = dev.get("name", "").lower()
                hostapi_info = sd.query_hostapis(dev["hostapi"])
                hostapi_name = hostapi_info.get("name", "").lower()

                # WASAPI loopback devices on Windows
                if "wasapi" in hostapi_name and dev["max_input_channels"] > 0:
                    if "loopback" in name or "stereo mix" in name or "what u hear" in name:
                        return i

            # Fallback: find any WASAPI input device (speakers often appear as loopback)
            for i, dev in enumerate(devices):
                hostapi_info = sd.query_hostapis(dev["hostapi"])
                hostapi_name = hostapi_info.get("name", "").lower()
                if "wasapi" in hostapi_name and dev["max_input_channels"] > 0:
                    name = dev.get("name", "").lower()
                    if "speaker" in name or "headphone" in name or "output" in name:
                        return i

        except Exception as e:
            print(f"Error finding loopback device: {e}")

        return None

    def get_available_devices(self):
        """Return list of available input devices for selection."""
        if sd is None:
            return []
        devices = []
        try:
            all_devs = sd.query_devices()
            for i, dev in enumerate(all_devs):
                if dev["max_input_channels"] > 0:
                    hostapi_info = sd.query_hostapis(dev["hostapi"])
                    devices.append({
                        "index": i,
                        "name": dev["name"],
                        "hostapi": hostapi_info.get("name", ""),
                        "channels": dev["max_input_channels"],
                        "sample_rate": dev["default_samplerate"],
                    })
        except Exception:
            pass
        return devices

    def _audio_callback(self, indata, frames, time_info, status):
        """Called by sounddevice for each audio block."""
        if status:
            pass  # could log overflow/underflow

        # Convert to mono float
        audio = indata[:, 0].copy() if indata.shape[1] > 1 else indata.flatten().copy()

        if self._enabled:
            result = self.compressor.process(audio)
        else:
            # Still compute levels for metering, but no gain reduction
            rms = np.sqrt(np.mean(audio ** 2))
            peak = np.max(np.abs(audio))
            result = {
                "input_rms_db": float(20.0 * np.log10(max(rms, 1e-10))),
                "input_peak_db": float(20.0 * np.log10(max(peak, 1e-10))),
                "gain_reduction_db": 0.0,
                "output_db": float(20.0 * np.log10(max(rms, 1e-10))),
                "target_volume_scalar": 1.0,
            }

        if self.callback:
            self.callback(result)

    def start(self, device_index=None):
        """Start audio monitoring."""
        if self._running:
            return

        if sd is None:
            print("sounddevice not available. Running in simulation mode.")
            self._start_simulation()
            return

        # Find device
        if device_index is None:
            device_index = self.find_loopback_device()

        if device_index is None:
            print("No loopback device found. Running in simulation mode.")
            print("On Windows, enable 'Stereo Mix' in Sound settings,")
            print("or install VB-Audio Virtual Cable for WASAPI loopback.")
            self._start_simulation()
            return

        try:
            dev_info = sd.query_devices(device_index)
            self._sample_rate = int(dev_info["default_samplerate"])
            self.compressor.sample_rate = self._sample_rate

            block_size = int(self._sample_rate * self.block_duration_ms / 1000)

            self._stream = sd.InputStream(
                device=device_index,
                channels=1,
                samplerate=self._sample_rate,
                blocksize=block_size,
                dtype="float32",
                callback=self._audio_callback,
            )
            self._stream.start()
            self._running = True
            print(f"Audio monitoring started on: {dev_info['name']}")

        except Exception as e:
            print(f"Failed to start audio capture: {e}")
            print("Falling back to simulation mode.")
            self._start_simulation()

    def _start_simulation(self):
        """
        Simulation mode for development/testing without audio hardware.
        Generates synthetic audio levels that mimic normal content with
        periodic commercial-like spikes.
        """
        self._running = True
        self._thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self._thread.start()

    def _simulation_loop(self):
        """Generate simulated audio data for testing."""
        t = 0
        while self._running:
            # Simulate normal audio around -20 to -15 dB with periodic spikes
            cycle = t % 30.0  # 30-second cycle

            if cycle < 20.0:
                # Normal content: -25 to -15 dB with some variation
                base_level = 0.04 + 0.02 * np.sin(t * 0.5)
                noise = np.random.randn(2048).astype(np.float32) * base_level
            else:
                # "Commercial" spike: -8 to -3 dB
                base_level = 0.15 + 0.1 * np.sin(t * 2.0)
                noise = np.random.randn(2048).astype(np.float32) * base_level

            # Add some dynamics
            noise *= (1.0 + 0.3 * np.sin(np.linspace(0, 4 * np.pi, 2048)))

            if self._enabled:
                result = self.compressor.process(noise)
            else:
                rms = np.sqrt(np.mean(noise ** 2))
                peak = np.max(np.abs(noise))
                result = {
                    "input_rms_db": float(20.0 * np.log10(max(rms, 1e-10))),
                    "input_peak_db": float(20.0 * np.log10(max(peak, 1e-10))),
                    "gain_reduction_db": 0.0,
                    "output_db": float(20.0 * np.log10(max(rms, 1e-10))),
                    "target_volume_scalar": 1.0,
                }

            if self.callback:
                self.callback(result)

            t += self.block_duration_ms / 1000.0
            time.sleep(self.block_duration_ms / 1000.0)

    def stop(self):
        """Stop audio monitoring."""
        self._running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def set_enabled(self, enabled: bool):
        """Enable/disable compression (metering continues)."""
        self._enabled = enabled

    def update_compressor(self, **kwargs):
        """Update compressor parameters."""
        self.compressor.update_params(**kwargs)

    @property
    def running(self):
        return self._running
