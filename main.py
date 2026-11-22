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


class Dilemma:
    def __init__(self, title: str, description: str, options: list):
        self.title = title
        self.description = description
        self.options = options


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

        self.pending_dilemma: Optional[Dilemma] = None
        self.dilemma_resolved = False

        if random.random() < 0.30:
            self.is_emergency = True
            self.pending_dilemma = self._generate_random_dilemma()

    def _generate_random_dilemma(self) -> Dilemma:
        scenarios = [
            Dilemma(
                "Panne Réacteur Droit",
                f"L'appareil {self.callsign} signale une chute de pression d'huile critique sur le réacteur droit.",
                [
                    ("Procédure d'urgence : Atterrissage immédiat", True,
                     "Atterrissage réussi sous escorte des pompiers. +1 500 $", 1500),
                    ("Tenter un redémarrage manuel des systèmes", False,
                     "Rupture du réacteur ! Amerrissage forcé hors piste.", -500),
                ]
            ),
            Dilemma(
                "Urgence Médicale à Bord",
                f"Un passager de {self.callsign} subit une crise grave. Le commandant demande une priorité absolue.",
                [
                    ("Créer un couloir aérien prioritaire immédiat", True,
                     "L'avion a atterri rapidement. Le passager est pris en charge ! +1 000 $", 1000),
                    ("Refuser pour maintenir le trafic régulier", True,
                     "L'avion a respecté la boucle d'attente sans incident majeur.", 300),
                ]
            ),
            Dilemma(
                "Transport d'Organes Vitaux",
                f"{self.callsign} transporte un cœur pour une greffe urgente et dispose d'une réserve de carburant limitée.",
                [
                    ("Accorder l'accès direct à la piste 09/27", True,
                     "Vol prioritaire complété avec succès ! Gratification : +2 000 $", 2000),
                    ("Placer l'avion en attente d'approche", False,
                     "Pénurie de carburant en approche, atterrissage très dangereux !", -1000),
                ]
            )
        ]
        return random.choice(scenarios)

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

        self.radar_level = 1
        self.radar_radius = 280
        self.radar_upgrade_cost = 3000
        self.scan_angle = 0.0

        self.spawn_timer = 0.0
        self.time_elapsed = 0.0
        self.airlines = ["AF", "LH", "BA", "TO", "EZ", "EK", "QR"]

    def upgrade_radar(self) -> bool:
        if self.money >= self.radar_upgrade_cost and self.radar_level < 3:
            self.money -= self.radar_upgrade_cost
            self.radar_level += 1
            self.radar_radius += 120
            self.radar_upgrade_cost = int(self.radar_upgrade_cost * 2.2)
            return True
        return False

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
        spawn_interval = max(2.5, 10.0 - (self.time_elapsed / 30.0))
        if self.spawn_timer >= spawn_interval:
            self.spawn_timer = 0.0
            if len(self.aircrafts) < 25:
                self.spawn_aircraft()

        for plane in self.aircrafts:
            plane.update(dt)

        self._check_collisions()
        self._check_landings()
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

    def _check_landings(self):
        for plane in self.aircrafts:
            if plane.is_landed or plane.has_crashed:
                continue

            dist = plane.position.distance_to(self.runway_pos)
            if dist < 45 and plane.altitude <= 500 and plane.speed <= 250:
                plane.is_landed = True
                self.landed_count += 1
                reward = 800 + (600 if plane.is_emergency else 0)
                self.money += reward
                self.score += 250

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

class DilemmaDialog(QDialog):
    def __init__(self, dilemma: Dilemma, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"🚨 URGENCE : {dilemma.title}")
        self.resize(450, 250)
        self.dilemma = dilemma
        self.selected_option_idx = -1

        layout = QVBoxLayout(self)

        desc = QLabel(dilemma.description)
        desc.setWordWrap(True)
        desc.setFont(QFont("Segoe UI", 10))
        layout.addWidget(desc)

        self.button_group = QButtonGroup(self)
        for idx, (opt_text, _, _, _) in enumerate(dilemma.options):
            rb = QRadioButton(opt_text)
            rb.setFont(QFont("Segoe UI", 9))
            self.button_group.addButton(rb, idx)
            layout.addWidget(rb)

        btn_confirm = QPushButton("Confirmer l'Instruction")
        btn_confirm.setStyleSheet("background-color: #1f6feb; font-weight: bold; padding: 8px;")
        btn_confirm.clicked.connect(self.accept_choice)
        layout.addWidget(btn_confirm)

    def accept_choice(self):
        self.selected_option_idx = self.button_group.checkedId()
        if self.selected_option_idx != -1:
            self.accept()
        else:
            QMessageBox.warning(self, "Attention", "Veuillez sélectionner une instruction.")


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

        # ---------------- PANEL GAUCHE ----------------
        left_panel = QVBoxLayout()

        stats_box = QGroupBox("FINANCES & PERFORMANCE")
        stats_layout = QVBoxLayout()
        self.lbl_money = QLabel("Argent : 0 $")
        self.lbl_score = QLabel("Score : 0")
        self.lbl_landed = QLabel("Atterrissages : 0")
        self.lbl_collisions = QLabel("Collisions : 0")

        for lbl in [self.lbl_money, self.lbl_score, self.lbl_landed, self.lbl_collisions]:
            lbl.setFont(QFont("Segoe UI", 10, QFont.Bold))
            stats_layout.addWidget(lbl)

        stats_box.setLayout(stats_layout)
        left_panel.addWidget(stats_box)

        plane_box = QGroupBox("AVIONS DÉTECTÉS")
        plane_layout = QVBoxLayout()
        self.plane_list_widget = QListWidget()
        self.plane_list_widget.itemClicked.connect(self.on_list_item_clicked)
        plane_layout.addWidget(self.plane_list_widget)
        plane_box.setLayout(plane_layout)
        left_panel.addWidget(plane_box)

        main_layout.addLayout(left_panel, stretch=1)

        # ---------------- RADAR CENTRAL ----------------
        self.radar = RadarWidget(self.manager)
        self.radar.aircraft_selected.connect(self.on_radar_aircraft_selected)
        main_layout.addWidget(self.radar, stretch=3)

        # ---------------- PANEL DROIT ----------------
        right_panel = QVBoxLayout()
        ctrl_box = QGroupBox("ORDRES DE TACTIQUE")
        ctrl_layout = QVBoxLayout()

        self.lbl_selected_plane = QLabel("Sélection : Aucun")
        self.lbl_selected_plane.setFont(QFont("Segoe UI", 11, QFont.Bold))
        ctrl_layout.addWidget(self.lbl_selected_plane)

        self.fuel_bar = QProgressBar()
        ctrl_layout.addWidget(QLabel("Carburant :"))
        ctrl_layout.addWidget(self.fuel_bar)

        self.btn_dilemma = QPushButton("RÉSOUDRE CRISE / DILEMME")
        self.btn_dilemma.clicked.connect(self.open_dilemma_modal)
        self.btn_dilemma.setEnabled(False)
        ctrl_layout.addWidget(self.btn_dilemma)

        ctrl_layout.addSpacing(10)

        btn_climb = QPushButton("Monter (+500m)")
        btn_descend = QPushButton("Descendre (-500m)")
        btn_turn_left = QPushButton("Cap +15° (Gauche)")
        btn_turn_right = QPushButton("Cap +15° (Droite)")
        btn_speed_up = QPushButton("Vitesse (+50 km/h)")
        btn_slow_down = QPushButton("Vitesse (-50 km/h)")
        btn_land = QPushButton("Approche Atterrissage")

        btn_climb.clicked.connect(lambda: self.send_instruction("CLIMB"))
        btn_descend.clicked.connect(lambda: self.send_instruction("DESCEND"))
        btn_turn_left.clicked.connect(lambda: self.send_instruction("LEFT"))
        btn_turn_right.clicked.connect(lambda: self.send_instruction("RIGHT"))
        btn_speed_up.clicked.connect(lambda: self.send_instruction("FASTER"))
        btn_slow_down.clicked.connect(lambda: self.send_instruction("SLOWER"))
        btn_land.clicked.connect(lambda: self.send_instruction("LAND"))

        for b in [btn_climb, btn_descend, btn_turn_left, btn_turn_right, btn_speed_up, btn_slow_down, btn_land]:
            ctrl_layout.addWidget(b)

        ctrl_layout.addStretch()
        ctrl_box.setLayout(ctrl_layout)
        right_panel.addWidget(ctrl_box)

        main_layout.addLayout(right_panel, stretch=1)

    # ---------------- LOGIQUE IHM ----------------

    def game_loop(self):
        self.manager.update(0.05)
        self.radar.update()

        self.lbl_money.setText(f"Budget : {self.manager.money} $")
        self.lbl_score.setText(f"Score : {self.manager.score}")
        self.lbl_landed.setText(f"Atterrissages : {self.manager.landed_count}")
        self.lbl_collisions.setText(f"Collisions : {self.manager.collisions_count}")

        self.sync_aircraft_list()
        self.update_control_panel()

    def sync_aircraft_list(self):
        self.plane_list_widget.clear()
        for plane in self.manager.aircrafts:
            status = ""
            if plane.pending_dilemma and not plane.dilemma_resolved:
                status = " [CRISE]"
            elif plane.is_emergency:
                status = " [URGENCE]"

            item = QListWidgetItem(f"{plane.callsign}{status} - {int(plane.altitude)}m")
            if plane.callsign == self.radar.selected_callsign:
                item.setSelected(True)
            self.plane_list_widget.addItem(item)

    def on_list_item_clicked(self, item: QListWidgetItem):
        callsign = item.text().split(" ")[0]
        self.radar.selected_callsign = callsign
        self.update_control_panel()

    def on_radar_aircraft_selected(self, callsign: str):
        self.update_control_panel()

    def update_control_panel(self):
        callsign = self.radar.selected_callsign
        plane = next((p for p in self.manager.aircrafts if p.callsign == callsign), None)

        if plane:
            self.lbl_selected_plane.setText(f"Sélection : {plane.callsign}")
            self.fuel_bar.setValue(int(plane.fuel))

            if plane.pending_dilemma and not plane.dilemma_resolved:
                self.btn_dilemma.setEnabled(True)
            else:
                self.btn_dilemma.setEnabled(False)
        else:
            self.lbl_selected_plane.setText("Sélection : Aucun")
            self.fuel_bar.setValue(0)
            self.btn_dilemma.setEnabled(False)

    def open_dilemma_modal(self):
        callsign = self.radar.selected_callsign
        plane = next((p for p in self.manager.aircrafts if p.callsign == callsign), None)

        if plane and plane.pending_dilemma and not plane.dilemma_resolved:
            dialog = DilemmaDialog(plane.pending_dilemma, self)
            if dialog.exec():
                opt_idx = dialog.selected_option_idx
                _, is_success, result_msg, reward = plane.pending_dilemma.options[opt_idx]

                plane.dilemma_resolved = True
                self.manager.money += reward

                if is_success:
                    QMessageBox.information(self, "Résultat de la Décision", f"RÉUSSITE :\n{result_msg}")
                else:
                    QMessageBox.critical(self, "Résultat de la Décision", f"ÉCHEC :\n{result_msg}")

    def send_instruction(self, action: str):
        callsign = self.radar.selected_callsign
        plane = next((p for p in self.manager.aircrafts if p.callsign == callsign), None)

        if not plane:
            return

        if action == "CLIMB":
            plane.target_altitude = min(10000, plane.target_altitude + 500)
        elif action == "DESCEND":
            plane.target_altitude = max(0, plane.target_altitude - 500)
        elif action == "LEFT":
            plane.target_heading = (plane.target_heading - 15) % 360
        elif action == "RIGHT":
            plane.target_heading = (plane.target_heading + 15) % 360
        elif action == "FASTER":
            plane.target_speed = min(900, plane.target_speed + 50)
        elif action == "SLOWER":
            plane.target_speed = max(180, plane.target_speed - 50)
        elif action == "LAND":
            runway = self.manager.runway_pos
            dx = runway.x - plane.position.x
            dy = runway.y - plane.position.y
            target_angle = math.degrees(math.atan2(dy, dx)) + 90
            plane.target_heading = target_angle % 360
            plane.target_altitude = 300
            plane.target_speed = 220


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
