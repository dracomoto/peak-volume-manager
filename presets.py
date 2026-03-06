"""
Peak Volume Manager - Preset Definitions
"""

PRESETS = {
    "Light": {
        "threshold": -18.0,
        "ratio": 2.0,
        "attack": 10.0,
        "release": 300.0,
        "knee": 30.0,
        "ceiling": -1.0,
        "output_gain": 0.0,
    },
    "Moderate": {
        "threshold": -24.0,
        "ratio": 4.0,
        "attack": 3.0,
        "release": 250.0,
        "knee": 20.0,
        "ceiling": -3.0,
        "output_gain": 0.0,
    },
    "Aggressive": {
        "threshold": -35.0,
        "ratio": 12.0,
        "attack": 1.0,
        "release": 150.0,
        "knee": 5.0,
        "ceiling": -6.0,
        "output_gain": 0.0,
    },
}

DEFAULT_PRESET = "Moderate"

CONTROL_RANGES = {
    "threshold": {"min": -60.0, "max": 0.0, "step": 0.5, "unit": "dB", "decimals": 1},
    "ratio": {"min": 1.0, "max": 20.0, "step": 0.5, "unit": ":1", "decimals": 1},
    "attack": {"min": 1.0, "max": 1000.0, "step": 1.0, "unit": "ms", "decimals": 0},
    "release": {"min": 10.0, "max": 1000.0, "step": 1.0, "unit": "ms", "decimals": 0},
    "knee": {"min": 0.0, "max": 40.0, "step": 0.5, "unit": "dB", "decimals": 1},
    "ceiling": {"min": -20.0, "max": 0.0, "step": 0.5, "unit": "dB", "decimals": 1},
    "output_gain": {"min": -12.0, "max": 12.0, "step": 0.5, "unit": "dB", "decimals": 1},
}
