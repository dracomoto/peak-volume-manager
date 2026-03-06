"""
Peak Volume Manager - Level Meter Widgets
Custom PyQt6 widgets for displaying audio levels with dB readouts.
"""

from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QFont


class LevelMeter(QWidget):
    """
    A horizontal level meter with dB scale and numeric readout.
    """

    def __init__(self, label: str = "Level", min_db: float = -60.0, max_db: float = 0.0,
                 color_normal: str = "#4CAF50", color_warn: str = "#FFC107",
                 color_clip: str = "#F44336", parent=None):
        super().__init__(parent)
        self.label_text = label
        self.min_db = min_db
        self.max_db = max_db
        self.color_normal = QColor(color_normal)
        self.color_warn = QColor(color_warn)
        self.color_clip = QColor(color_clip)
        self._level_db = min_db
        self._peak_db = min_db
        self._peak_hold_count = 0

        self.setMinimumHeight(28)
        self.setMaximumHeight(36)

        # Layout with label and dB readout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._label = QLabel(label)
        self._label.setFixedWidth(70)
        self._label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        font = QFont()
        font.setPointSize(9)
        self._label.setFont(font)
        layout.addWidget(self._label)

        self._bar = _MeterBar(self.min_db, self.max_db,
                              self.color_normal, self.color_warn, self.color_clip)
        layout.addWidget(self._bar, stretch=1)

        self._readout = QLabel(f"{self.min_db:.1f} dB")
        self._readout.setFixedWidth(72)
        self._readout.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        readout_font = QFont("Consolas", 9)
        self._readout.setFont(readout_font)
        layout.addWidget(self._readout)

    def set_level(self, db: float):
        """Update the displayed level."""
        self._level_db = max(self.min_db, min(self.max_db, db))

        # Peak hold
        if self._level_db > self._peak_db:
            self._peak_db = self._level_db
            self._peak_hold_count = 0
        else:
            self._peak_hold_count += 1
            if self._peak_hold_count > 30:  # ~0.5 sec at 60fps
                self._peak_db = max(self._peak_db - 0.5, self._level_db)

        self._bar.set_level(self._level_db, self._peak_db)
        self._readout.setText(f"{self._level_db:+.1f} dB")


class _MeterBar(QWidget):
    """Internal bar widget for the level meter."""

    def __init__(self, min_db, max_db, color_normal, color_warn, color_clip, parent=None):
        super().__init__(parent)
        self.min_db = min_db
        self.max_db = max_db
        self.color_normal = color_normal
        self.color_warn = color_warn
        self.color_clip = color_clip
        self._level = 0.0
        self._peak = 0.0
        self.setMinimumHeight(18)
        self.setMaximumHeight(24)

    def set_level(self, level_db: float, peak_db: float):
        self._level = (level_db - self.min_db) / (self.max_db - self.min_db)
        self._peak = (peak_db - self.min_db) / (self.max_db - self.min_db)
        self._level = max(0.0, min(1.0, self._level))
        self._peak = max(0.0, min(1.0, self._peak))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()

        # Background
        painter.fillRect(0, 0, w, h, QColor("#2a2a2a"))

        # Level bar with gradient
        bar_width = int(w * self._level)
        if bar_width > 0:
            gradient = QLinearGradient(0, 0, w, 0)
            gradient.setColorAt(0.0, self.color_normal)
            gradient.setColorAt(0.6, self.color_normal)
            gradient.setColorAt(0.8, self.color_warn)
            gradient.setColorAt(1.0, self.color_clip)
            painter.fillRect(QRectF(0, 2, bar_width, h - 4), gradient)

        # Peak indicator
        peak_x = int(w * self._peak)
        if peak_x > 0:
            peak_color = self.color_clip if self._peak > 0.9 else self.color_warn
            painter.fillRect(QRectF(peak_x - 2, 0, 2, h), peak_color)

        # Scale marks at -40, -20, -10, -6, -3, 0
        painter.setPen(QColor("#666666"))
        for db in [-40, -20, -10, -6, -3, 0]:
            x = int(w * (db - self.min_db) / (self.max_db - self.min_db))
            painter.drawLine(x, 0, x, 3)
            painter.drawLine(x, h - 3, x, h)

        # Border
        painter.setPen(QColor("#555555"))
        painter.drawRect(0, 0, w - 1, h - 1)
        painter.end()


class GainReductionMeter(LevelMeter):
    """
    Specialized meter for showing gain reduction (displays in reverse).
    Shows 0 dB on the right (no reduction) and negative values growing left.
    """

    def __init__(self, parent=None):
        super().__init__(
            label="Reduction",
            min_db=-30.0,
            max_db=0.0,
            color_normal="#FF9800",
            color_warn="#FF5722",
            color_clip="#D32F2F",
            parent=parent,
        )

    def set_level(self, db: float):
        """Update with gain reduction value (negative = more reduction)."""
        clamped = max(self.min_db, min(0.0, db))
        self._level_db = clamped
        # For reduction meter, we show the magnitude
        magnitude = abs(clamped)
        fraction = magnitude / abs(self.min_db)
        self._bar._level = max(0.0, min(1.0, fraction))
        self._bar._peak = self._bar._level
        self._bar.update()
        self._readout.setText(f"{clamped:+.1f} dB")
