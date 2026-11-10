import sys
import math
import random
from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, QPointF, Signal, QObject
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QTransform,
    QConicalGradient
)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QProgressBar, QMessageBox, QDialog, QRadioButton, QButtonGroup
)


# ==============================================================================
# 0. GÉNÉRATEUR AUTOMATIQUE DE TEXTURES & SPRITES (IMAGES)
# ==============================================================================


# ==============================================================================
# 1. MODÈLE DE DONNÉES & LOGIQUE MÉTIER
# ==============================================================================

@dataclass
class Vector2D:
    x: float
    y: float

    def distance_to(self, other: 'Vector2D') -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


class Aircraft:
    def __init__(self, callsign: str, position: Vector2D, heading: float, altitude: float, speed: float):
        self.callsign = callsign
        self.position = position
        self.heading = heading
        self.target_heading = heading
        self.altitude = altitude
        self.target_altitude = altitude
        self.speed = speed
        self.target_speed = speed
        self.fuel = random.uniform(40, 100)
        self.is_emergency = False
        self.is_landed = False
        self.has_crashed = False


    def update(self, dt: float):
        if self.is_landed or self.has_crashed:
            return

        self.fuel = max(0, self.fuel - 0.04 * dt)

        if abs(self.heading - self.target_heading) > 0.5:
            diff = (self.target_heading - self.heading + 540) % 360 - 180
            self.heading += (1 if diff > 0 else -1) * min(35 * dt, abs(diff))
            self.heading %= 360

        if abs(self.altitude - self.target_altitude) > 5:
            step = 350 * dt
            self.altitude += step if self.altitude < self.target_altitude else -step

        if abs(self.speed - self.target_speed) > 1:
            step = 25 * dt
            self.speed += step if self.speed < self.target_speed else -step

        speed_units = (self.speed / 10.0) * dt
        rad = math.radians(self.heading - 90)
        self.position.x += math.cos(rad) * speed_units
        self.position.y += math.sin(rad) * speed_units


# ==============================================================================
# 2. DIALOGUE DE DÉCISION / DILEMME
# ==============================================================================


# ==============================================================================
# 3. VUE RADAR AVEC DÉZOOM AUTOMATIQUE
# ==============================================================================


# ==============================================================================
# 4. INTERFACE PRINCIPALE & CONTRÔLES
# ==============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ipsa - Tour de controle")
        self.resize(1150, 720)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
