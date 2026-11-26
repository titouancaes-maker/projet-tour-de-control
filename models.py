import math
import random
from dataclasses import dataclass
from typing import List, Optional

from PySide6.QtCore import QObject, Signal


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

        self.fuel -= 0.04 * dt
        if self.fuel <= 0:
            self.fuel = 0
            self.has_crashed = True
            return

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
