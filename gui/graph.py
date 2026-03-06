"""
Peak Volume Manager - Real-time Level History Graph
Scrolling graph showing input vs output levels over time.
"""

import numpy as np
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QFont, QPainterPath


class LevelGraph(QWidget):
    """
    Scrolling time-series graph showing input and output audio levels.
    Displays the last N seconds of data.
    """

    def __init__(self, history_seconds: float = 10.0, updates_per_second: float = 20.0,
                 parent=None):
        super().__init__(parent)
        self.history_seconds = history_seconds
        self.updates_per_second = updates_per_second
        self.max_points = int(history_seconds * updates_per_second)
        self.min_db = -60.0
        self.max_db = 0.0

        # Data buffers
        self._input_history = np.full(self.max_points, self.min_db, dtype=np.float64)
        self._output_history = np.full(self.max_points, self.min_db, dtype=np.float64)
        self._reduction_history = np.zeros(self.max_points, dtype=np.float64)

        self.setMinimumHeight(150)

        # Colors
        self.bg_color = QColor("#1e1e1e")
        self.grid_color = QColor("#333333")
        self.input_color = QColor("#42A5F5")     # blue
        self.output_color = QColor("#66BB6A")    # green
        self.reduction_color = QColor("#FF7043")  # orange
        self.text_color = QColor("#aaaaaa")
        self.threshold_color = QColor("#FFC107")  # yellow dashed line

        self._threshold_db = -24.0
        self._ceiling_db = -3.0

    def set_threshold(self, db: float):
        self._threshold_db = db
        self.update()

    def set_ceiling(self, db: float):
        self._ceiling_db = db
        self.update()

    def add_data(self, input_db: float, output_db: float, reduction_db: float):
        """Add a new data point and scroll."""
        self._input_history = np.roll(self._input_history, -1)
        self._input_history[-1] = input_db

        self._output_history = np.roll(self._output_history, -1)
        self._output_history[-1] = output_db

        self._reduction_history = np.roll(self._reduction_history, -1)
        self._reduction_history[-1] = reduction_db

        self.update()

    def _db_to_y(self, db: float, h: int, margin_top: int = 20, margin_bottom: int = 25) -> float:
        """Convert dB value to Y pixel coordinate."""
        plot_h = h - margin_top - margin_bottom
        ratio = (db - self.min_db) / (self.max_db - self.min_db)
        ratio = max(0.0, min(1.0, ratio))
        return margin_top + plot_h * (1.0 - ratio)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        margin_left = 45
        margin_right = 10
        margin_top = 20
        margin_bottom = 25
        plot_w = w - margin_left - margin_right
        plot_h = h - margin_top - margin_bottom

        # Background
        painter.fillRect(0, 0, w, h, self.bg_color)

        # Grid lines and dB labels
        painter.setPen(QPen(self.grid_color, 1))
        label_font = QFont("Consolas", 8)
        painter.setFont(label_font)
        for db in [-50, -40, -30, -20, -10, -6, -3, 0]:
            y = self._db_to_y(db, h, margin_top, margin_bottom)
            painter.setPen(QPen(self.grid_color, 1, Qt.PenStyle.DotLine))
            painter.drawLine(margin_left, int(y), w - margin_right, int(y))
            painter.setPen(self.text_color)
            painter.drawText(2, int(y) + 4, f"{db:+.0f}")

        # Threshold line (dashed yellow)
        threshold_y = self._db_to_y(self._threshold_db, h, margin_top, margin_bottom)
        pen = QPen(self.threshold_color, 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(margin_left, int(threshold_y), w - margin_right, int(threshold_y))

        # Ceiling line (dashed red)
        ceiling_y = self._db_to_y(self._ceiling_db, h, margin_top, margin_bottom)
        pen = QPen(QColor("#F44336"), 1, Qt.PenStyle.DashLine)
        painter.setPen(pen)
        painter.drawLine(margin_left, int(ceiling_y), w - margin_right, int(ceiling_y))

        # Draw data traces
        if self.max_points > 1:
            self._draw_trace(painter, self._input_history, self.input_color,
                             margin_left, plot_w, h, margin_top, margin_bottom, width=1.5)
            self._draw_trace(painter, self._output_history, self.output_color,
                             margin_left, plot_w, h, margin_top, margin_bottom, width=2.0)

        # Legend
        painter.setFont(label_font)
        legend_y = h - 6
        painter.setPen(self.input_color)
        painter.drawText(margin_left + 5, legend_y, "— Input")
        painter.setPen(self.output_color)
        painter.drawText(margin_left + 65, legend_y, "— Output")
        painter.setPen(self.threshold_color)
        painter.drawText(margin_left + 135, legend_y, "-- Threshold")
        painter.setPen(QColor("#F44336"))
        painter.drawText(margin_left + 225, legend_y, "-- Ceiling")

        # Title
        painter.setPen(self.text_color)
        title_font = QFont("", 9)
        title_font.setBold(True)
        painter.setFont(title_font)
        painter.drawText(margin_left, 14, "Level History (10 sec)")

        # Plot border
        painter.setPen(QPen(QColor("#555555"), 1))
        painter.drawRect(margin_left, margin_top, plot_w, plot_h)

        painter.end()

    def _draw_trace(self, painter, data, color, margin_left, plot_w, h,
                    margin_top, margin_bottom, width=1.5):
        """Draw a data trace on the graph."""
        pen = QPen(color, width)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)

        n = len(data)
        if n < 2:
            return

        path = QPainterPath()
        x_step = plot_w / (n - 1)
        first = True

        for i in range(n):
            x = margin_left + i * x_step
            y = self._db_to_y(data[i], h, margin_top, margin_bottom)
            if first:
                path.moveTo(x, y)
                first = False
            else:
                path.lineTo(x, y)

        painter.drawPath(path)

    def clear(self):
        """Clear all history data."""
        self._input_history.fill(self.min_db)
        self._output_history.fill(self.min_db)
        self._reduction_history.fill(0.0)
        self.update()
