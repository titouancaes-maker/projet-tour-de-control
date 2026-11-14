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

class AssetManager:
    """Génère et stocke en mémoire les images/textures de la piste et des avions."""

    _airplane_pixmap: Optional[QPixmap] = None
    _runway_pixmap: Optional[QPixmap] = None

    @classmethod
    def get_airplane_sprite(cls) -> QPixmap:
        if cls._airplane_pixmap is not None:
            return cls._airplane_pixmap

        pix = QPixmap(60, 60)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        p.setRenderHint(QPainter.Antialiasing)

        # Ombre portée de l'avion
        p.setBrush(QBrush(QColor(0, 0, 0, 80)))
        p.setPen(Qt.NoPen)
        p.drawEllipse(18, 22, 24, 28)

        # Fuselage principal
        p.setBrush(QBrush(QColor(240, 243, 246)))
        p.setPen(QPen(QColor(180, 190, 200), 1))
        p.drawRoundedRect(26, 5, 8, 50, 4, 4)

        # Ailes principales
        p.setBrush(QBrush(QColor(220, 225, 230)))
        p.drawPolygon([QPointF(30, 20), QPointF(5, 38), QPointF(12, 42), QPointF(30, 28)])
        p.drawPolygon([QPointF(30, 20), QPointF(55, 38), QPointF(48, 42), QPointF(30, 28)])

        # Empennage
        p.drawPolygon([QPointF(30, 45), QPointF(18, 54), QPointF(18, 57), QPointF(30, 52)])
        p.drawPolygon([QPointF(30, 45), QPointF(42, 54), QPointF(42, 57), QPointF(30, 52)])

        # Cockpit
        p.setBrush(QBrush(QColor(20, 100, 180)))
        p.drawEllipse(27, 10, 6, 8)

        p.end()
        cls._airplane_pixmap = pix
        return pix

    @classmethod
    def get_runway_texture(cls) -> QPixmap:
        if cls._runway_pixmap is not None:
            return cls._runway_pixmap

        pix = QPixmap(180, 50)
        p = QPainter(pix)

        p.fillRect(0, 0, 180, 50, QColor(40, 42, 45))

        p.setPen(QPen(QColor(255, 255, 255), 2))
        p.drawLine(0, 3, 180, 3)
        p.drawLine(0, 47, 180, 47)

        p.setPen(QPen(QColor(255, 255, 255), 2, Qt.DashLine))
        p.drawLine(0, 25, 180, 25)

        p.setPen(QPen(QColor(255, 255, 255), 2))
        for i in range(8, 43, 6):
            p.drawLine(10, i, 25, i)
            p.drawLine(155, i, 170, i)

        p.end()
        cls._runway_pixmap = pix
        return pix


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


class AirspaceManager(QObject):
    simulation_updated = Signal()

    def __init__(self, width: int = 800, height: int = 600):
        super().__init__()
        self.width = width
        self.height = height
        self.aircrafts: List[Aircraft] = []
        self.runway_pos = Vector2D(width / 2, height / 2)

        self.money = 2000
        self.score = 0
        self.landed_count = 0
        self.collisions_count = 0

        self.radar_radius = 280
        self.scan_angle = 0.0

        self.spawn_timer = 0.0
        self.time_elapsed = 0.0
        self.airlines = ["AF", "LH", "BA", "TO", "EZ", "EK", "QR"]

    def spawn_aircraft(self):
        callsign = f"{random.choice(self.airlines)}{random.randint(100, 999)}"
        spawn_dist = self.radar_radius + 20
        angle = random.uniform(0, 2 * math.pi)

        px = self.width / 2 + math.cos(angle) * spawn_dist
        py = self.height / 2 + math.sin(angle) * spawn_dist

        center_angle = math.degrees(math.atan2(self.height / 2 - py, self.width / 2 - px)) + 90
        heading = center_angle % 360

        alt = random.choice([2000, 3000, 4000])
        spd = random.choice([350, 400, 450])
        self.aircrafts.append(Aircraft(callsign, Vector2D(px, py), heading, alt, spd))

    def update(self, dt: float):
        self.time_elapsed += dt
        self.scan_angle = (self.scan_angle + 180 * dt) % 360

        self.spawn_timer += dt
        if self.spawn_timer >= 5.0:
            self.spawn_timer = 0.0
            self.spawn_aircraft()

        for plane in self.aircrafts:
            plane.update(dt)

        self._clean_up()

        self.simulation_updated.emit()

    def _clean_up(self):
        max_dist = self.radar_radius + 150
        center = self.runway_pos
        self.aircrafts = [
            p for p in self.aircrafts
            if not p.is_landed and not p.has_crashed and p.position.distance_to(center) <= max_dist
        ]


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




