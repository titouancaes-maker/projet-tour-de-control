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

        self._check_collisions()
        self._clean_up()

        self.simulation_updated.emit()

    def _check_collisions(self):
        n = len(self.aircrafts)
        for i in range(n):
            for j in range(i + 1, n):
                p1, p2 = self.aircrafts[i], self.aircrafts[j]
                if p1.is_landed or p2.is_landed:
                    continue

                dist = p1.position.distance_to(p2.position)
                if dist < 28 and abs(p1.altitude - p2.altitude) < 300:
                    p1.has_crashed = True
                    p2.has_crashed = True
                    self.collisions_count += 1
                    self.money = max(0, self.money - 2000)

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

class RadarWidget(QWidget):
    def __init__(self, manager: AirspaceManager):
        super().__init__()
        self.manager = manager
        self.setMinimumSize(600, 600)

        self.plane_sprite = AssetManager.get_airplane_sprite()
        self.runway_texture = AssetManager.get_runway_texture()

    def _get_scale_factor(self) -> float:
        """Calcule le facteur de dézoom pour que tout le radar tienne à l'écran."""
        base_radius = 280.0
        # Réduit la taille d'affichage au fur et à mesure que le rayon grandit
        return base_radius / self.manager.radar_radius

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        cx, cy = self.width() / 2, self.height() / 2
        scale = self._get_scale_factor()
        r_drawn = self.manager.radar_radius * scale  # Rayon affiché à l'écran

        # Fond Radar sombre
        painter.fillRect(self.rect(), QColor("#080c10"))

        # Cercles de portée ajustés à l'échelle
        pen_grid = QPen(QColor(0, 255, 65, 40), 1, Qt.DashLine)
        painter.setPen(pen_grid)
        for step in range(80, int(self.manager.radar_radius) + 1, 80):
            step_scaled = step * scale
            painter.drawEllipse(QPointF(cx, cy), step_scaled, step_scaled)

        painter.setPen(QPen(QColor(0, 255, 65, 180), 2))
        painter.drawEllipse(QPointF(cx, cy), r_drawn, r_drawn)

        # Affichage de la piste d'atterrissage à l'échelle
        r_pos = self.manager.runway_pos
        rw_w = self.runway_texture.width() * scale
        rw_h = self.runway_texture.height() * scale
        painter.drawPixmap(
            int(cx - rw_w / 2), int(cy - rw_h / 2),
            int(rw_w), int(rw_h),
            self.runway_texture
        )

        # Balayage radar rotatif
        sweep_grad = QConicalGradient(QPointF(cx, cy), -self.manager.scan_angle)
        sweep_grad.setColorAt(0.0, QColor(0, 255, 65, 80))
        sweep_grad.setColorAt(0.15, QColor(0, 255, 65, 20))
        sweep_grad.setColorAt(0.3, QColor(0, 255, 65, 0))
        sweep_grad.setColorAt(1.0, QColor(0, 255, 65, 0))

        painter.setBrush(QBrush(sweep_grad))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(QPointF(cx, cy), r_drawn, r_drawn)

        rad_angle = math.radians(self.manager.scan_angle)
        lx = cx + math.cos(rad_angle) * r_drawn
        ly = cy + math.sin(rad_angle) * r_drawn
        painter.setPen(QPen(QColor(0, 255, 65, 220), 2))
        painter.drawLine(int(cx), int(cy), int(lx), int(ly))

        # Dessin des avions recalculés selon le zoom
        for plane in self.manager.aircrafts:
            if plane.position.distance_to(r_pos) <= self.manager.radar_radius:
                self._draw_aircraft(painter, plane, cx, cy, scale)

    def _draw_aircraft(self, painter: QPainter, plane: Aircraft, cx: float, cy: float, scale: float):
        r_pos = self.manager.runway_pos

        # Repositionnement selon l'échelle
        screen_x = cx + (plane.position.x - r_pos.x) * scale
        screen_y = cy + (plane.position.y - r_pos.y) * scale

        alt_offset = (plane.altitude / 1000.0) * 2.5 * scale

        painter.save()

        # Applique la translation et le dézoom au sprite de l'avion
        transform = QTransform()
        transform.translate(screen_x, screen_y - alt_offset)
        transform.scale(scale, scale)
        transform.rotate(plane.heading)
        transform.translate(-self.plane_sprite.width() / 2, -self.plane_sprite.height() / 2)

        painter.setTransform(transform, combine=True)
        painter.drawPixmap(0, 0, self.plane_sprite)
        painter.restore()

        color = QColor(0, 255, 65)
        # Étiquette
        painter.setPen(QPen(color))
        painter.setFont(QFont("Consolas", 8))
        label = f"{plane.callsign}\n{int(plane.altitude)}m | {int(plane.speed)}km/h\nFL:{int(plane.fuel)}%"
        painter.drawText(int(screen_x + (16 * scale)), int(screen_y - alt_offset + 4), label)


# ==============================================================================
# 4. INTERFACE PRINCIPALE & CONTRÔLES
# ==============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ipsa - Tour de controle")
        self.resize(1150, 720)

        self.manager = AirspaceManager(700, 680)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(50)

        self._init_ui()

    def _init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)

        # ---------------- RADAR CENTRAL ----------------
        self.radar = RadarWidget(self.manager)
        main_layout.addWidget(self.radar, stretch=3)

    # ---------------- LOGIQUE IHM ----------------

    def game_loop(self):
        self.manager.update(0.05)
        self.radar.update()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
