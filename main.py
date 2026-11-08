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
