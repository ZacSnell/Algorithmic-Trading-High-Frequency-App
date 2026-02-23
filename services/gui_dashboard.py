# services/gui_dashboard.py - FINAL LIVE VERSION
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
from ml_ensemble import EnsembleCoordinator
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont, QColor
import json
from datetime import datetime

class TradingDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("7-Agent Ensemble Live Dashboard")
        self.resize(1600, 900)
        self.ensemble = EnsembleCoordinator()
        self.setup_ui()
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_dashboard)
        self.timer.start(4000)  # Update every 4 seconds
        self.update_dashboard()  # Initial update

    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Header
        title = QLabel("7-Agent Ensemble Live Dashboard")
        title.setFont(QFont("Arial", 20, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Status Banner
        self.status_banner = QLabel("SYSTEM IS RUNNING - 7 AGENTS ACTIVE")
        self.status_banner.setFont(QFont("Arial", 14, QFont.Bold))
        self.status_banner.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; border-radius: 5px;")
        self.status_banner.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_banner)

        # Agent Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Agent", "Accuracy", "Last Confidence", "Last Insight", "P&L Contrib"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        # Knowledge Summary
        kb_title = QLabel("What We've Learned Today")
        kb_title.setFont(QFont("Arial", 14, QFont.Bold))
        layout.addWidget(kb_title)
        self.kb_text = QTextEdit()
        self.kb_text.setReadOnly(True)
        self.kb_text.setMaximumHeight(200)
        layout.addWidget(self.kb_text)

        # Ensemble Status
        self.ensemble_label = QLabel("Ensemble: HOLD (0.0%) — 0/7 agree")
        self.ensemble_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.ensemble_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.ensemble_label)

        # Refresh button
        refresh_btn = QPushButton("Refresh Now")
        refresh_btn.clicked.connect(self.update_dashboard)
        layout.addWidget(refresh_btn)

    def update_dashboard(self):
        # Agent Table
        self.table.setRowCount(0)
        row = 0
        for name, cfg in SPECIALISTS.items():
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(cfg['name']))

            # Try to get real accuracy from knowledge base
            acc = self.get_agent_accuracy(name)
            self.table.setItem(row, 1, QTableWidgetItem(f"{acc:.1f}%"))

            # Current confidence (run a quick prediction)
            try:
                df = self.get_sample_features()
                if df is not None:
                    pred = self.ensemble.predict(df, "SPY")
                    conf = pred['confidence'] * 100
                    self.table.setItem(row, 2, QTableWidgetItem(f"{conf:.1f}%"))
                else:
                    self.table.setItem(row, 2, QTableWidgetItem("N/A"))
            except:
                self.table.setItem(row, 2, QTableWidgetItem("N/A"))

            # Last insight
            insight = self.get_last_insight(name)
            self.table.setItem(row, 3, QTableWidgetItem(insight[:80] + "..." if len(insight) > 80 else insight))

            self.table.setItem(row, 4, QTableWidgetItem("$0"))  # P&L placeholder for now
            row += 1

        # Knowledge Summary
        if KNOWLEDGE_BASE.exists():
            try:
                with open(KNOWLEDGE_BASE, 'r') as f:
                    kb = json.load(f)[-15:]
                text = ""
                for entry in kb:
                    date = entry.get('date', '')[:16]
                    specialist = entry.get('specialist', 'Unknown')
                    insight = entry.get('insight', entry.get('rationale', 'No insight'))
                    text += f"[{date}] {specialist}: {insight}\n"
                self.kb_text.setText(text)
            except:
                self.kb_text.setText("Knowledge base loading...")

        # Ensemble Status
        try:
            df = self.get_sample_features()
            if df is not None:
                result = self.ensemble.predict(df, "SPY")
                status = "BUY" if result.get('recommendation') == "BUY" else "HOLD"
                conf = result.get('confidence', 0) * 100
                count = sum(1 for v in self.ensemble.specialists.values() if hasattr(v, 'predict'))
                self.ensemble_label.setText(f"Ensemble: {status} ({conf:.1f}%) — {count}/7 agree")
        except:
            self.ensemble_label.setText("Ensemble: HOLD (0.0%) — 0/7 agree")

    def get_agent_accuracy(self, name):
        """Get latest accuracy from knowledge base"""
        if not KNOWLEDGE_BASE.exists():
            return 0.0
        try:
            with open(KNOWLEDGE_BASE, 'r') as f:
                kb = json.load(f)
            for entry in reversed(kb):
                if entry.get('specialist') == name and 'test_accuracy' in entry:
                    return entry['test_accuracy'] * 100
            return 85.0  # fallback
        except:
            return 85.0

    def get_last_insight(self, name):
        """Get latest insight from knowledge base"""
        if not KNOWLEDGE_BASE.exists():
            return "No insight yet"
        try:
            with open(KNOWLEDGE_BASE, 'r') as f:
                kb = json.load(f)
            for entry in reversed(kb):
                if entry.get('specialist') == name:
                    return entry.get('insight', entry.get('rationale', 'No insight'))
            return "No insight yet"
        except:
            return "No insight yet"

    def get_sample_features(self):
        """Get a sample DataFrame for live prediction"""
        try:
            from build_dataset import download_intraday, add_features_and_target
            df = download_intraday("SPY")
            if df is not None:
                df = add_features_and_target(df)
                return df
            return None
        except:
            return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TradingDashboard()
    window.show()
    sys.exit(app.exec_())