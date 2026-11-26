import math

from PySide6.QtCore import QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QGroupBox, QProgressBar, QMessageBox
)

from models import AirspaceManager
from radar_widget import RadarWidget
from dilemma_dialog import DilemmaDialog


# ==============================================================================
# 4. INTERFACE PRINCIPALE & CONTRÔLES
# ==============================================================================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IPSA - Tour de Contrôle : Extended Radar & Graphic Simulation")
        self.resize(1150, 720)

        self.manager = AirspaceManager(700, 680)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.game_loop)
        self.timer.start(50)

        self._init_ui()
        self.apply_stylesheet()

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

        self.lbl_money.setStyleSheet("color: #2ea043;")
        stats_box.setLayout(stats_layout)
        left_panel.addWidget(stats_box)

        shop_box = QGroupBox("EXTENSIONS TOUR DE CONTRÔLE")
        shop_layout = QVBoxLayout()
        self.btn_upgrade_radar = QPushButton("Améliorer Radar (3 000 $)")
        self.btn_upgrade_radar.setStyleSheet("background-color: #238636; font-weight: bold;")
        self.btn_upgrade_radar.clicked.connect(self.buy_radar_upgrade)
        self.lbl_radar_info = QLabel("Niveau Radar : 1 (Portée: 280px)")

        shop_layout.addWidget(self.lbl_radar_info)
        shop_layout.addWidget(self.btn_upgrade_radar)
        shop_box.setLayout(shop_layout)
        left_panel.addWidget(shop_box)

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

        self.btn_dilemma = QPushButton("⚠️ RÉSOUDRE CRISE / DILEMME")
        self.btn_dilemma.setStyleSheet("background-color: #da3633; font-weight: bold; padding: 10px;")
        self.btn_dilemma.clicked.connect(self.open_dilemma_modal)
        self.btn_dilemma.setEnabled(False)
        ctrl_layout.addWidget(self.btn_dilemma)

        ctrl_layout.addSpacing(10)

        btn_climb = QPushButton("▲ Monter (+500m)")
        btn_descend = QPushButton("▼ Descendre (-500m)")
        btn_turn_left = QPushButton("◄ Cap +15° (Gauche)")
        btn_turn_right = QPushButton("► Cap +15° (Droite)")
        btn_speed_up = QPushButton("⚡ Vitesse (+50 km/h)")
        btn_slow_down = QPushButton("⚓ Vitesse (-50 km/h)")
        btn_land = QPushButton("🛬 Approche Atterrissage")
        btn_land.setStyleSheet("background-color: #1f6feb; font-weight: bold;")

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

        self.btn_upgrade_radar.setText(f"Agrandir Radar ({self.manager.radar_upgrade_cost} $)")
        self.lbl_radar_info.setText(
            f"Niveau Radar : {self.manager.radar_level} (Portée: {self.manager.radar_radius}px)")

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

    def buy_radar_upgrade(self):
        if self.manager.upgrade_radar():
            QMessageBox.information(self, "Extension de Portée",
                                    "Portée du radar et vue d'ensemble agrandies avec succès !")
        else:
            QMessageBox.warning(self, "Fonds Insuffisants", "Fonds insuffisants pour étendre la couverture du radar.")

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

    def apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
                font-family: 'Segoe UI', sans-serif;
            }
            QGroupBox {
                border: 1px solid #30363d;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: #58a6ff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
            }
            QPushButton {
                background-color: #21262d;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px;
                color: #c9d1d9;
            }
            QPushButton:hover {
                background-color: #30363d;
                border-color: #8b949e;
            }
            QPushButton:disabled {
                background-color: #161b22;
                color: #484f58;
            }
            QListWidget {
                background-color: #161b22;
                border: 1px solid #30363d;
            }
            QListWidget::item:selected {
                background-color: #1f6feb;
                color: white;
            }
            QProgressBar {
                border: 1px solid #30363d;
                border-radius: 3px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #238636;
            }
        """)
