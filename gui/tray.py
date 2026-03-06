"""
Peak Volume Manager - System Tray
System tray icon with right-click menu for minimize/restore/toggle/quit.
"""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt6.QtCore import pyqtSignal, QObject


def create_default_icon(size: int = 64, active: bool = True) -> QIcon:
    """Create a simple programmatic icon since we don't have icon files."""
    pixmap = QPixmap(size, size)
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    bg_color = QColor("#2196F3") if active else QColor("#9E9E9E")
    painter.setBrush(bg_color)
    painter.setPen(QColor("#FFFFFF"))
    painter.drawEllipse(2, 2, size - 4, size - 4)

    # "PV" text
    painter.setPen(QColor("#FFFFFF"))
    font = QFont("Arial", int(size * 0.3))
    font.setBold(True)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), 0x0084, "PV")  # AlignCenter

    painter.end()
    return QIcon(pixmap)


class SystemTray(QObject):
    """
    System tray icon with context menu.
    """

    show_requested = pyqtSignal()
    toggle_requested = pyqtSignal()
    quit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._enabled = True

        # Create tray icon
        self._icon_active = create_default_icon(64, active=True)
        self._icon_inactive = create_default_icon(64, active=False)

        self._tray = QSystemTrayIcon(self._icon_active)
        self._tray.setToolTip("Peak Volume Manager")
        self._tray.activated.connect(self._on_activated)

        # Context menu
        self._menu = QMenu()
        self._toggle_action = self._menu.addAction("Disable")
        self._toggle_action.triggered.connect(self.toggle_requested.emit)
        self._menu.addSeparator()
        self._show_action = self._menu.addAction("Show Window")
        self._show_action.triggered.connect(self.show_requested.emit)
        self._menu.addSeparator()
        self._quit_action = self._menu.addAction("Quit")
        self._quit_action.triggered.connect(self.quit_requested.emit)

        self._tray.setContextMenu(self._menu)

    def show(self):
        self._tray.show()

    def hide(self):
        self._tray.hide()

    def set_enabled(self, enabled: bool):
        """Update tray icon and menu text based on enabled state."""
        self._enabled = enabled
        if enabled:
            self._tray.setIcon(self._icon_active)
            self._toggle_action.setText("Disable")
            self._tray.setToolTip("Peak Volume Manager - Active")
        else:
            self._tray.setIcon(self._icon_inactive)
            self._toggle_action.setText("Enable")
            self._tray.setToolTip("Peak Volume Manager - Disabled")

    def show_message(self, title: str, message: str):
        """Show a system notification."""
        self._tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 3000)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_requested.emit()
