from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QMessageBox, QRadioButton, QButtonGroup
)

from models import Dilemma


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
