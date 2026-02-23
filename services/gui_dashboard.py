# services/gui_dashboard.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from ml_ensemble import EnsembleCoordinator
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont
import json
import pandas as pd

class TradingDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Algorithmic Trading - 7-Agent Live Dashboard")
        self.resize(1600, 900)
        self.ensemble = EnsembleCoordinator()
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(3000)  # update every 3 seconds
        self.update_dashboard()

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        title = QLabel("7-Agent Ensemble Live Dashboard")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Agent Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Agent", "Accuracy", "Last Confidence", "Last Insight", "P&L Contrib"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        # Knowledge Summary
        kb_title = QLabel("What We've Learned Today")
        kb_title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(kb_title)
        self.kb_text = QTextEdit()
        self.kb_text.setReadOnly(True)
        layout.addWidget(self.kb_text)

        # Ensemble Status
        self.status_label = QLabel("Ensemble: HOLD")
        self.status_label.setFont(QFont("Arial", 16, QFont.Bold))
        layout.addWidget(self.status_label)

    def update_dashboard(self):
        # Agent Table
        self.table.setRowCount(len(SPECIALISTS))
        row = 0
        for name, cfg in SPECIALISTS.items():
            self.table.setItem(row, 0, QTableWidgetItem(cfg['name']))
            self.table.setItem(row, 1, QTableWidgetItem("Calculating..."))
            self.table.setItem(row, 2, QTableWidgetItem("Calculating..."))
            self.table.setItem(row, 3, QTableWidgetItem("Calculating..."))
            self.table.setItem(row, 4, QTableWidgetItem("Calculating..."))
            row += 1

        # Knowledge Base Summary
        if KNOWLEDGE_BASE.exists():
            try:
                with open(KNOWLEDGE_BASE) as f:
                    kb = json.load(f)[-15:]
                text = "\n".join([f"[{e.get('date','')[:16]}] {e.get('specialist','')} : {e.get('insight','')[:120]}" for e in kb])
                self.kb_text.setText(text)
            except:
                self.kb_text.setText("Knowledge base loading...")

        # Ensemble Status (demo - you can call predict on last bar if wanted)
        self.status_label.setText("Ensemble: HOLD (0.0%) — 0/7 agree")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingDashboard()
    window.show()
    sys.exit(app.exec_())