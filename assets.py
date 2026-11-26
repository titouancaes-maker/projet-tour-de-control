from typing import Optional

from PySide6.QtCore import Qt, QPointF
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QPixmap


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
