import math
from typing import Optional

from PySide6.QtCore import Qt, QPointF, Signal
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QTransform, QConicalGradient
)
from PySide6.QtWidgets import QWidget

from assets import AssetManager
from models import AirspaceManager, Aircraft, Vector2D


# ==============================================================================
# 3. VUE RADAR AVEC DÉZOOM AUTOMATIQUE
# ==============================================================================

class RadarWidget(QWidget):
    aircraft_selected = Signal(str)

    def __init__(self, manager: AirspaceManager):
        super().__init__()
        self.manager = manager
        self.selected_callsign: Optional[str] = None
        self.setMinimumSize(600, 600)

        self.plane_sprite = AssetManager.get_airplane_sprite()
        self.runway_texture = AssetManager.get_runway_texture()

    def _get_scale_factor(self) -> float:
        """Calcule le facteur de dézoom pour que tout le radar tienne à l'écran."""
        base_radius = 280.0
        # Réduit la taille d'affichage au fur et à mesure que le rayon grandit
        return base_radius / self.manager.radar_radius

    def mousePressEvent(self, event):
        cx, cy = self.width() / 2, self.height() / 2
        scale = self._get_scale_factor()

        # Transformation du clic écran vers le repère virtuel du monde
        click_x = (event.position().x() - cx) / scale + self.manager.runway_pos.x
        click_y = (event.position().y() - cy) / scale + self.manager.runway_pos.y
        click_pos = Vector2D(click_x, click_y)

        selected = None
        for plane in self.manager.aircrafts:
            if plane.position.distance_to(click_pos) < (30 / scale):
                selected = plane.callsign
                break

        self.selected_callsign = selected
        if selected:
            self.aircraft_selected.emit(selected)
        self.update()

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

        is_sel = (plane.callsign == self.selected_callsign)
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
        if plane.is_emergency:
            color = QColor(255, 50, 50)
        elif is_sel:
            color = QColor(0, 210, 255)

        if is_sel:
            painter.setPen(QPen(QColor(0, 210, 255), 1.5, Qt.DashLine))
            painter.drawEllipse(QPointF(screen_x, screen_y - alt_offset), 20 * scale, 20 * scale)

        # Étiquette
        painter.setPen(QPen(color))
        painter.setFont(QFont("Consolas", 8))
        dilemma_tag = " [!]" if (plane.pending_dilemma and not plane.dilemma_resolved) else ""
        label = f"{plane.callsign}{dilemma_tag}\n{int(plane.altitude)}m | {int(plane.speed)}km/h\nFL:{int(plane.fuel)}%"
        painter.drawText(int(screen_x + (16 * scale)), int(screen_y - alt_offset + 4), label)
