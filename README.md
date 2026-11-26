# Simulateur de tour de contrôle

Projet GP211 – IPSA, année 2026-2027. Simulation gamifiée de contrôle aérien en Python 3.12 avec PySide6 : le joueur guide les avions qui entrent dans son secteur jusqu'à la piste, sans collision, en gérant les urgences et son budget.

## Installation et lancement

```bash
pip install -r requirements.txt
python main.py
```

## Structure du projet

Le code est réparti en **un fichier par partie de travail**. Les imports vont toujours dans le même sens (`main.py` → `main_window.py` → `radar_widget.py` / `dilemma_dialog.py` → `models.py` / `assets.py`), ce qui évite les imports circulaires.

| Fichier | Classes | Rôle | Responsable |
| --- | --- | --- | --- |
| `assets.py` | AssetManager | dessine l'avion et la piste en code | Personne A |
| `models.py` | Vector2D, Dilemma, Aircraft, AirspaceManager | état des avions, règles du jeu (collisions, atterrissages, budget) | Personne B |
| `radar_widget.py` | RadarWidget | affichage du radar, sélection à la souris | Personne A |
| `dilemma_dialog.py` | DilemmaDialog | fenêtre de choix pendant une crise | Personne A |
| `main_window.py` | MainWindow | panneaux, boutons, boucle de jeu (QTimer) | Personne A |
| `main.py` | (aucune) | point d'entrée : crée l'application et affiche la fenêtre | commun |

Autres fichiers : `docs/uml_classes.md` (diagramme UML), `requirements.txt`, `.gitignore`.

## Modules et bibliothèques utilisés

| Module | Utilisation |
| --- | --- |
| PySide6.QtWidgets | fenêtres, panneaux, boutons, liste, barre de carburant, boîtes de dialogue |
| PySide6.QtGui | dessin du radar (QPainter), sprites (QPixmap), rotation des avions (QTransform), balayage (QConicalGradient) |
| PySide6.QtCore | horloge de jeu (QTimer, 20 images/s), signaux (Signal) |
| math | trigonométrie des caps, distances |
| random | apparition des avions, compagnies, urgences |
| dataclasses, typing | classe Vector2D, annotations de type |

## Guide d'utilisation

1. **Sélectionner un avion** : cliquer dessus sur le radar ou dans la liste « Avions détectés ». Le panneau de droite affiche son indicatif et son carburant.
2. **Donner un ordre** : monter ou descendre de 500 m, tourner de 15°, accélérer ou ralentir de 50 km/h. L'avion rejoint progressivement la valeur demandée.
3. **Faire atterrir** : « Approche Atterrissage » oriente l'avion vers la piste, le fait descendre à 300 m et ralentir à 220 km/h. L'atterrissage est validé à moins de 45 px du centre de la piste, sous 500 m et sous 250 km/h : +800 $ (+600 $ si l'avion était en urgence) et +250 points.
4. **Éviter les collisions** : deux avions à moins de 28 px et moins de 300 m d'écart d'altitude sont détruits, et le budget perd 2 000 $.
5. **Gérer les crises** : les avions marqués [!] sur le radar ou [CRISE] dans la liste attendent une décision. Le bouton rouge ouvre le dilemme, et le choix fait gagner ou perdre de l'argent.
6. **Améliorer le radar** : le bouton d'extension augmente la portée de 120 px, jusqu'au niveau 3 (premier achat 3 000 $, puis prix ×2,2).
7. **Difficulté** : un nouvel avion apparaît toutes les 10 s au début, puis de plus en plus souvent jusqu'à toutes les 2,5 s, avec 25 avions au maximum.
