"""
Peak Volume Manager - Controls Panel
Slider controls for compressor parameters with preset selection.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QComboBox,
    QGroupBox, QGridLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont

from presets import PRESETS, CONTROL_RANGES


class ControlSlider(QWidget):
    """A labeled slider with numeric readout."""

    valueChanged = pyqtSignal(str, float)  # param_name, value

    def __init__(self, param_name: str, parent=None):
        super().__init__(parent)
        self.param_name = param_name
        info = CONTROL_RANGES[param_name]
        self._min = info["min"]
        self._max = info["max"]
        self._step = info["step"]
        self._unit = info["unit"]
        self._decimals = info["decimals"]

        # Number of slider steps
        self._steps = int((self._max - self._min) / self._step)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(8)

        # Label
        display_name = param_name.replace("_", " ").title()
        self._label = QLabel(display_name)
        self._label.setFixedWidth(85)
        self._label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        font = QFont()
        font.setPointSize(9)
        self._label.setFont(font)
        layout.addWidget(self._label)

        # Slider
        self._slider = QSlider(Qt.Orientation.Horizontal)
        self._slider.setMinimum(0)
        self._slider.setMaximum(self._steps)
        self._slider.setTickPosition(QSlider.TickPosition.NoTicks)
        self._slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self._slider, stretch=1)

        # Value readout
        self._readout = QLabel("")
        self._readout.setFixedWidth(80)
        self._readout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        readout_font = QFont("Consolas", 9)
        self._readout.setFont(readout_font)
        layout.addWidget(self._readout)

        # Initialize
        self.set_value(self._min)

    def _on_slider_changed(self, slider_pos: int):
        value = self._min + slider_pos * self._step
        self._update_readout(value)
        self.valueChanged.emit(self.param_name, value)

    def _update_readout(self, value: float):
        if self._decimals == 0:
            text = f"{value:.0f} {self._unit}"
        else:
            text = f"{value:.{self._decimals}f} {self._unit}"
        self._readout.setText(text)

    def set_value(self, value: float):
        """Set the slider value programmatically."""
        value = max(self._min, min(self._max, value))
        slider_pos = int((value - self._min) / self._step)
        self._slider.blockSignals(True)
        self._slider.setValue(slider_pos)
        self._slider.blockSignals(False)
        self._update_readout(value)

    def get_value(self) -> float:
        return self._min + self._slider.value() * self._step


class ControlsPanel(QWidget):
    """
    Complete controls panel with preset selector and parameter sliders.
    """

    paramChanged = pyqtSignal(str, float)    # param_name, value
    presetChanged = pyqtSignal(str)          # preset_name

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sliders = {}
        self._suppress_signals = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Preset row
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        preset_label.setFixedWidth(50)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        preset_label.setFont(font)
        preset_layout.addWidget(preset_label)

        self._preset_combo = QComboBox()
        self._preset_combo.addItems(list(PRESETS.keys()) + ["Custom"])
        self._preset_combo.currentTextChanged.connect(self._on_preset_selected)
        preset_layout.addWidget(self._preset_combo)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # Sliders group
        group = QGroupBox("Compressor Controls")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(2)

        for param_name in CONTROL_RANGES:
            slider = ControlSlider(param_name)
            slider.valueChanged.connect(self._on_slider_value_changed)
            self._sliders[param_name] = slider
            group_layout.addWidget(slider)

        layout.addWidget(group)

    def _on_preset_selected(self, preset_name: str):
        if preset_name in PRESETS and not self._suppress_signals:
            self.load_preset(preset_name)
            self.presetChanged.emit(preset_name)

    def _on_slider_value_changed(self, param_name: str, value: float):
        if not self._suppress_signals:
            # Switch to Custom if user manually adjusts
            self._suppress_signals = True
            self._preset_combo.setCurrentText("Custom")
            self._suppress_signals = False
            self.paramChanged.emit(param_name, value)

    def load_preset(self, preset_name: str):
        """Load a preset's values into all sliders."""
        if preset_name not in PRESETS:
            return
        self._suppress_signals = True
        preset = PRESETS[preset_name]
        for param_name, value in preset.items():
            if param_name in self._sliders:
                self._sliders[param_name].set_value(value)
        self._preset_combo.setCurrentText(preset_name)
        self._suppress_signals = False

    def set_values(self, values: dict):
        """Set slider values from a dict."""
        self._suppress_signals = True
        for param_name, value in values.items():
            if param_name in self._sliders:
                self._sliders[param_name].set_value(value)
        self._suppress_signals = False

    def get_values(self) -> dict:
        """Get all current slider values."""
        return {name: slider.get_value() for name, slider in self._sliders.items()}

    def get_preset(self) -> str:
        return self._preset_combo.currentText()
