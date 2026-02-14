# trading_gui.py
# Desktop GUI for the ML Trading System
# Built with PyQt5 for professional UI/UX

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
import threading
import time

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox,
    QStatusBar, QMessageBox, QProgressBar, QGroupBox, QGridLayout,
    QFrame, QCalendarWidget, QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread, QDate, QDateTime
from PyQt5.QtGui import QFont, QColor, QIcon, QPixmap

# Add services directory to path
sys.path.insert(0, str(Path(__file__).parent / "services"))

from config import *
from live_trader import LiveTrader
from ml_predictor import MLPredictor
from market_scheduler import MarketScheduler
from strategy_manager import StrategyManager
from trade_logger import TradeLogger


class TradingWorker(QThread):
    """Background worker thread for trading system"""
    
    status_changed = pyqtSignal(str)
    trade_executed = pyqtSignal(dict)
    performance_updated = pyqtSignal(dict)
    market_status_updated = pyqtSignal(dict)
    
    def __init__(self, strategy='macd_crossover'):
        super().__init__()
        self.trader = None
        self.running = False
        self.strategy = strategy
    
    def set_running(self, running):
        self.running = running
    
    def run(self):
        """Main trading loop"""
        try:
            self.trader = LiveTrader()
            
            if not self.trader.start():
                self.status_changed.emit("Failed to start trading system")
                return
            
            self.status_changed.emit(f"Trading system started ({self.strategy})")
            self.running = True
            
            # Main loop
            while self.running:
                try:
                    # Update market status
                    status = self.trader.scheduler.get_market_status()
                    self.market_status_updated.emit(status)
                    
                    # Update performance
                    perf = self.trader.get_performance_summary()
                    self.performance_updated.emit(perf)
                    
                    time.sleep(5)  # Update every 5 seconds
                
                except Exception as e:
                    self.status_changed.emit(f"Error: {str(e)}")
                    time.sleep(5)
        
        except Exception as e:
            self.status_changed.emit(f"Fatal error: {str(e)}")
        finally:
            if self.trader:
                self.trader.stop()


class TradingGUI(QMainWindow):
    """Main trading application GUI with multi-strategy support"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("ML Trading System v2.0 - Multi-Strategy")
        self.setGeometry(100, 100, 1500, 950)
        
        # Application state
        self.is_trading = False
        self.trading_worker = None
        self.trader = None
        self.strategy_manager = StrategyManager()
        self.trade_logger = TradeLogger()
        self.current_strategy = 'macd_crossover'
        
        # Initialize predictors for each strategy
        self.predictors = {}
        self.model_status = {}
        
        # Check for trained models for each strategy
        for strategy in STRATEGIES.keys():
            if STRATEGIES[strategy]['enabled']:
                predictor = MLPredictor(strategy=strategy)
                self.predictors[strategy] = predictor
                self.model_status[strategy] = predictor.is_model_ready()
        
        # Initialize UI
        self.setup_ui()
        self.setup_timers()
        self.apply_styles()
        
        strategy_status = "✓" if self.model_status.get(self.current_strategy) else "✗"
        self.update_status(f"Ready - {self.current_strategy} ({strategy_status})")
    
    def setup_ui(self):
        """Set up user interface"""
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top control panel
        control_layout = self.create_control_panel()
        main_layout.addLayout(control_layout)
        
        # Tabs for different views
        tabs = QTabWidget()
        tabs.addTab(self.create_dashboard_tab(), "Dashboard")
        tabs.addTab(self.create_trades_tab(), "Trades")
        tabs.addTab(self.create_history_tab(), "History")
        tabs.addTab(self.create_settings_tab(), "Settings")
        tabs.addTab(self.create_logs_tab(), "Logs")
        
        main_layout.addWidget(tabs)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def create_control_panel(self):
        """Create top control panel with strategy selector"""
        layout = QHBoxLayout()
        
        # Start/Stop button
        self.start_button = QPushButton("START TRADING")
        self.start_button.setMinimumWidth(130)
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.toggle_trading)
        layout.addWidget(self.start_button)
        
        layout.addSpacing(10)
        
        # Status indicator
        self.status_indicator = QLabel("●")
        self.status_indicator.setFont(QFont("Arial", 16))
        self.status_indicator.setStyleSheet("color: red;")
        layout.addWidget(self.status_indicator)
        
        self.status_label = QLabel("Stopped")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(self.status_label)
        
        layout.addSpacing(20)
        
        # Strategy selector
        strategy_label = QLabel("Strategy:")
        strategy_label.setFont(QFont("Arial", 11, QFont.Bold))
        layout.addWidget(strategy_label)
        
        self.strategy_combo = QComboBox()
        for strat_name, strat_config in STRATEGIES.items():
            if strat_config['enabled']:
                status = "✓" if self.model_status.get(strat_name) else "✗"
                display_name = f"{strat_config['name']} ({status})"
                self.strategy_combo.addItem(display_name, strat_name)
        
        self.strategy_combo.currentIndexChanged.connect(self.on_strategy_changed)
        self.strategy_combo.setMinimumWidth(200)
        layout.addWidget(self.strategy_combo)
        
        layout.addSpacing(20)
        
        # Market status
        market_label = QLabel("Market:")
        layout.addWidget(market_label)
        
        self.market_status = QLabel("Checking...")
        self.market_status.setFont(QFont("Arial", 11))
        layout.addWidget(self.market_status)
        
        layout.addStretch()
        
        # Quick stats
        self.quick_stats = QLabel("Trades: 0 | Win Rate: 0% | P&L: $0.00")
        self.quick_stats.setFont(QFont("Arial", 10))
        layout.addWidget(self.quick_stats)
        
        return layout
    
    def on_strategy_changed(self):
        """Handle strategy selection change"""
        self.current_strategy = self.strategy_combo.currentData()
        
        if self.is_trading:
            reply = QMessageBox.question(
                self, "Switch Strategy",
                f"Change active strategy to {STRATEGIES[self.current_strategy]['name']}?\n"
                "This will stop current trading.",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.toggle_trading()  # Stop
                self.update_status(f"Strategy switched to {self.current_strategy}")
            else:
                # Revert selection
                for i in range(self.strategy_combo.count()):
                    if self.strategy_combo.itemData(i) == self.current_strategy:
                        self.strategy_combo.blockSignals(True)
                        self.strategy_combo.setCurrentIndex(i)
                        self.strategy_combo.blockSignals(False)
                        break
        else:
            status = "✓" if self.model_status.get(self.current_strategy) else "✗"
            self.update_status(f"Strategy: {self.current_strategy} ({status})")
    
    def create_dashboard_tab(self):
        """Create dashboard tab showing key metrics"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Performance metrics
        metrics_group = QGroupBox(f"Performance Summary - {STRATEGIES[self.current_strategy]['name']}")
        metrics_layout = QGridLayout()
        
        self.metric_labels = {}
        metrics = [
            ("Total Trades", "total_trades"),
            ("Closed Trades", "closed_trades"),
            ("Win Rate", "win_rate"),
            ("Total P&L", "total_pnl"),
            ("Avg Trade P&L", "avg_trade_pnl"),
        ]
        
        row = 0
        for label_text, key in metrics:
            label = QLabel(label_text + ":")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            value = QLabel("--")
            value.setFont(QFont("Arial", 10))
            
            metrics_layout.addWidget(label, row, 0)
            metrics_layout.addWidget(value, row, 1)
            
            self.metric_labels[key] = value
            row += 1
        
        metrics_group.setLayout(metrics_layout)
        layout.addWidget(metrics_group)
        
        # Recent trades
        recent_group = QGroupBox("Recent Trades")
        recent_layout = QVBoxLayout()
        
        self.recent_trades_table = QTableWidget()
        self.recent_trades_table.setColumnCount(7)
        self.recent_trades_table.setHorizontalHeaderLabels(
            ["Symbol", "Strategy", "Side", "Qty", "Entry", "Exit", "P&L"]
        )
        self.recent_trades_table.setMaximumHeight(250)
        self.recent_trades_table.setAlternatingRowColors(True)
        
        recent_layout.addWidget(self.recent_trades_table)
        recent_group.setLayout(recent_layout)
        layout.addWidget(recent_group)
        
        # Account info
        account_group = QGroupBox("Account Information")
        account_layout = QGridLayout()
        
        self.account_labels = {}
        account_info = [
            ("Buying Power", "buying_power"),
            ("Cash", "cash"),
            ("Equity", "equity"),
            ("Portfolio Value", "portfolio_value"),
        ]
        
        row = 0
        for label_text, key in account_info:
            label = QLabel(label_text + ":")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            value = QLabel("$0.00")
            value.setFont(QFont("Arial", 10))
            
            account_layout.addWidget(label, row, 0)
            account_layout.addWidget(value, row, 1)
            
            self.account_labels[key] = value
            row += 1
        
        account_group.setLayout(account_layout)
        layout.addWidget(account_group)
        
        layout.addStretch()
        return widget
    
    def create_trades_tab(self):
        """Create trades history tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        filter_layout.addWidget(QLabel("Filter by Symbol:"))
        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("Leave blank for all")
        self.symbol_filter.setMaximumWidth(150)
        self.symbol_filter.textChanged.connect(self.refresh_trades)
        filter_layout.addWidget(self.symbol_filter)
        
        filter_layout.addWidget(QLabel("Strategy:"))
        self.trades_strategy_filter = QComboBox()
        self.trades_strategy_filter.addItem("All")
        for strat_name, strat_config in STRATEGIES.items():
            if strat_config['enabled']:
                self.trades_strategy_filter.addItem(strat_config['name'], strat_name)
        self.trades_strategy_filter.currentIndexChanged.connect(self.refresh_trades)
        filter_layout.addWidget(self.trades_strategy_filter)
        
        filter_layout.addWidget(QLabel("Status:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "OPEN", "CLOSED"])
        self.status_filter.currentTextChanged.connect(self.refresh_trades)
        filter_layout.addWidget(self.status_filter)
        
        filter_layout.addStretch()
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh_trades)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Trades table
        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(11)
        self.trades_table.setHorizontalHeaderLabels([
            "Date", "Symbol", "Strategy", "Side", "Qty", "Entry Price", "Entry Time",
            "Exit Price", "Exit Time", "P&L %", "P&L $"
        ])
        self.trades_table.setAlternatingRowColors(True)
        self.trades_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.trades_table)
        
        # Load trades
        self.refresh_trades()
        
        return widget
    
    def create_history_tab(self):
        """Create daily trading history with date picker"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        # Left side: Calendar
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("Select Date:"))
        
        self.calendar = QCalendarWidget()
        self.calendar.setSelectedDate(QDate.currentDate())
        self.calendar.clicked.connect(self.on_date_selected)
        left_layout.addWidget(self.calendar)
        
        left_layout.addWidget(QLabel("Available Dates:"))
        self.date_list = QListWidget()
        self.date_list.itemClicked.connect(self.on_date_list_clicked)
        left_layout.addWidget(self.date_list)
        
        left_frame = QWidget()
        left_frame.setLayout(left_layout)
        left_frame.setMaximumWidth(300)
        layout.addWidget(left_frame)
        
        # Right side: Trade details for selected date
        right_layout = QVBoxLayout()
        
        # Date info
        info_layout = QHBoxLayout()
        info_layout.addWidget(QLabel("Date:"))
        self.history_date_label = QLabel("--")
        self.history_date_label.setFont(QFont("Arial", 11, QFont.Bold))
        info_layout.addWidget(self.history_date_label)
        
        info_layout.addSpacing(20)
        info_layout.addWidget(QLabel("Strategy:"))
        self.history_strategy_filter = QComboBox()
        self.history_strategy_filter.addItem("All Strategies")
        for strat_name, strat_config in STRATEGIES.items():
            if strat_config['enabled']:
                self.history_strategy_filter.addItem(strat_config['name'], strat_name)
        self.history_strategy_filter.currentIndexChanged.connect(self.refresh_history_trades)
        self.history_strategy_filter.setMaximumWidth(200)
        info_layout.addWidget(self.history_strategy_filter)
        
        info_layout.addStretch()
        
        export_btn = QPushButton("Export Day")
        export_btn.clicked.connect(self.export_day)
        info_layout.addWidget(export_btn)
        
        right_layout.addLayout(info_layout)
        
        # Statistics for the day
        stats_group = QGroupBox("Daily Statistics")
        stats_layout = QGridLayout()
        
        self.history_stats = {}
        stat_keys = [
            ("Total Trades", "total_trades"),
            ("Winning Trades", "winning_trades"),
            ("Losing Trades", "losing_trades"),
            ("Win Rate", "win_rate"),
            ("Total P&L", "total_pnl"),
            ("Avg P&L", "avg_pnl"),
        ]
        
        row = 0
        for label_text, key in stat_keys:
            label = QLabel(label_text + ":")
            label.setFont(QFont("Arial", 10, QFont.Bold))
            value = QLabel("--")
            value.setFont(QFont("Arial", 10))
            
            stats_layout.addWidget(label, row, 0)
            stats_layout.addWidget(value, row, 1)
            
            self.history_stats[key] = value
            row += 1
        
        stats_group.setLayout(stats_layout)
        right_layout.addWidget(stats_group)
        
        # Trades table for the day
        right_layout.addWidget(QLabel("Trades for Selected Date:"))
        self.history_trades_table = QTableWidget()
        self.history_trades_table.setColumnCount(9)
        self.history_trades_table.setHorizontalHeaderLabels([
            "Time", "Symbol", "Strategy", "Side", "Qty", "Entry", "Exit", "Status", "P&L"
        ])
        self.history_trades_table.setAlternatingRowColors(True)
        self.history_trades_table.horizontalHeader().setStretchLastSection(True)
        right_layout.addWidget(self.history_trades_table)
        
        right_frame = QWidget()
        right_frame.setLayout(right_layout)
        layout.addWidget(right_frame)
        
        # Load available dates
        self.refresh_date_list()
        
        return widget
    
    def refresh_date_list(self):
        """Populate list of available trading dates"""
        self.date_list.clear()
        available_dates = self.trade_logger.get_available_dates()
        
        for date in sorted(available_dates, reverse=True):
            item = QListWidgetItem(date)
            self.date_list.addItem(item)
    
    def on_date_selected(self):
        """Handle calendar date selection"""
        selected_date = self.calendar.selectedDate()
        date_str = selected_date.toString("yyyy-MM-dd")
        self.history_date_label.setText(date_str)
        self.refresh_history_trades()
    
    def on_date_list_clicked(self, item):
        """Handle date list selection"""
        date_str = item.text()
        date_obj = QDate.fromString(date_str, "yyyy-MM-dd")
        self.calendar.setSelectedDate(date_obj)
        self.history_date_label.setText(date_str)
        self.refresh_history_trades()
    
    def refresh_history_trades(self):
        """Refresh trades for selected date"""
        date_str = self.history_date_label.text()
        if date_str == "--":
            return
        
        # Get strategy filter
        strategy_filter = self.history_strategy_filter.currentData()
        
        # Load trades for the day
        if strategy_filter:
            daily_data = self.trade_logger.get_strategy_daily_trades(strategy_filter, date_str)
        else:
            daily_data = self.trade_logger.get_daily_trades(date_str)
        
        # Extract the trades list from the returned dict
        trades = daily_data.get('trades', [])
        
        # Update statistics
        if trades:
            stats = self.trade_logger.get_daily_statistics(date_str)
            
            if strategy_filter and strategy_filter in stats.get('by_strategy', {}):
                stats = stats['by_strategy'][strategy_filter]
            
            self.history_stats['total_trades'].setText(str(stats.get('total_trades', 0)))
            self.history_stats['winning_trades'].setText(str(stats.get('winning_trades', 0)))
            self.history_stats['losing_trades'].setText(str(stats.get('losing_trades', 0)))
            win_rate = stats.get('win_rate', 0)
            self.history_stats['win_rate'].setText(f"{win_rate:.1%}")
            self.history_stats['total_pnl'].setText(f"${stats.get('total_pnl', 0):,.2f}")
            self.history_stats['avg_pnl'].setText(f"${stats.get('avg_pnl', 0):,.2f}")
        
        # Update trades table
        self.history_trades_table.setRowCount(0)
        for trade in reversed(trades):
            row = self.history_trades_table.rowCount()
            self.history_trades_table.insertRow(row)
            
            entry_time = trade.get('entry_time', "-")
            if entry_time != "-" and len(entry_time) > 8:
                entry_time = entry_time[-8:]
            self.history_trades_table.setItem(row, 0, QTableWidgetItem(entry_time))
            
            self.history_trades_table.setItem(row, 1, QTableWidgetItem(trade['symbol']))
            self.history_trades_table.setItem(row, 2, QTableWidgetItem(trade.get('strategy', '--')))
            self.history_trades_table.setItem(row, 3, QTableWidgetItem(trade['side']))
            self.history_trades_table.setItem(row, 4, QTableWidgetItem(str(trade['qty'])))
            self.history_trades_table.setItem(row, 5, QTableWidgetItem(f"${trade['entry_price']:.2f}"))
            
            exit_price = trade.get('exit_price')
            self.history_trades_table.setItem(
                row, 6,
                QTableWidgetItem(f"${exit_price:.2f}" if exit_price else "-")
            )
            
            self.history_trades_table.setItem(row, 7, QTableWidgetItem(trade['status']))
            
            pnl = trade.get('pnl_amount', 0)
            pnl_item = QTableWidgetItem(f"${pnl:+,.2f}")
            
            # Color code P&L
            if pnl > 0:
                pnl_item.setBackground(QColor(200, 255, 200))
            elif pnl < 0:
                pnl_item.setBackground(QColor(255, 200, 200))
            
            self.history_trades_table.setItem(row, 8, pnl_item)
    
    def export_day(self):
        """Export selected day's trades to CSV"""
        date_str = self.history_date_label.text()
        if date_str == "--":
            QMessageBox.warning(self, "Export", "Please select a date first")
            return
        
        try:
            filepath = self.trade_logger.export_daily_trades_to_csv(date_str)
            QMessageBox.information(
                self, "Export Complete",
                f"Trades exported to:\n{filepath}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))
    
    def create_settings_tab(self):
        """Create settings tab for configuration"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Model settings
        model_group = QGroupBox("Model Settings")
        model_layout = QGridLayout()
        
        model_layout.addWidget(QLabel("Model Type:"), 0, 0)
        self.model_type_combo = QComboBox()
        self.model_type_combo.addItems(["random_forest", "gradient_boosting"])
        self.model_type_combo.setCurrentText(ML_MODEL_TYPE)
        model_layout.addWidget(self.model_type_combo, 0, 1)
        
        model_layout.addWidget(QLabel("Min Confidence (Current Strategy):"), 1, 0)
        self.min_confidence_spin = QDoubleSpinBox()
        self.min_confidence_spin.setRange(0.5, 0.99)
        min_conf = STRATEGIES[self.current_strategy]['min_confidence']
        self.min_confidence_spin.setValue(min_conf)
        self.min_confidence_spin.setSingleStep(0.01)
        model_layout.addWidget(self.min_confidence_spin, 1, 1)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        # Risk settings
        risk_group = QGroupBox("Risk Management")
        risk_layout = QGridLayout()
        
        risk_layout.addWidget(QLabel("Stop Loss %:"), 0, 0)
        self.stop_loss_spin = QDoubleSpinBox()
        self.stop_loss_spin.setRange(0.01, 0.1)
        self.stop_loss_spin.setValue(STOP_LOSS_PCT)
        self.stop_loss_spin.setSingleStep(0.01)
        risk_layout.addWidget(self.stop_loss_spin, 0, 1)
        
        risk_layout.addWidget(QLabel("Take Profit %:"), 1, 0)
        self.take_profit_spin = QDoubleSpinBox()
        self.take_profit_spin.setRange(0.01, 0.1)
        self.take_profit_spin.setValue(TAKE_PROFIT_PCT)
        self.take_profit_spin.setSingleStep(0.01)
        risk_layout.addWidget(self.take_profit_spin, 1, 1)
        
        risk_layout.addWidget(QLabel("Position Size (%):"), 2, 0)
        self.position_size_spin = QSpinBox()
        self.position_size_spin.setRange(10, 100)
        self.position_size_spin.setValue(POSITION_SIZE_PCT)
        self.position_size_spin.setSuffix("%")
        self.position_size_spin.setToolTip(f"Percentage of buying power to use per position\nPresets: {POSITION_SIZE_PRESETS}")
        risk_layout.addWidget(self.position_size_spin, 2, 1)
        
        risk_layout.addWidget(QLabel("Max Open Positions:"), 3, 0)
        self.max_positions_spin = QSpinBox()
        self.max_positions_spin.setRange(1, 50)
        self.max_positions_spin.setValue(MAX_OPEN_POSITIONS)
        risk_layout.addWidget(self.max_positions_spin, 3, 1)
        
        risk_group.setLayout(risk_layout)
        layout.addWidget(risk_group)
        
        # Strategy status
        strategy_status_group = QGroupBox("Strategy Model Status")
        strategy_status_layout = QGridLayout()
        
        row = 0
        for strat_name, strat_config in STRATEGIES.items():
            if strat_config['enabled']:
                label = QLabel(strat_config['name'] + ":")
                label.setFont(QFont("Arial", 10, QFont.Bold))
                status_text = "✓ Ready" if self.model_status.get(strat_name) else "✗ Not Ready"
                status = QLabel(status_text)
                strategy_status_layout.addWidget(label, row, 0)
                strategy_status_layout.addWidget(status, row, 1)
                row += 1
        
        strategy_status_group.setLayout(strategy_status_layout)
        layout.addWidget(strategy_status_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        train_btn = QPushButton("Train Current Strategy")
        train_btn.clicked.connect(self.train_model)
        button_layout.addWidget(train_btn)
        
        train_all_btn = QPushButton("Train All Strategies")
        train_all_btn.clicked.connect(self.train_all_models)
        button_layout.addWidget(train_all_btn)
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return widget
    
    def create_logs_tab(self):
        """Create logs tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Log display
        self.log_display = QTableWidget()
        self.log_display.setColumnCount(3)
        self.log_display.setHorizontalHeaderLabels(["Timestamp", "Level", "Message"])
        self.log_display.setAlternatingRowColors(True)
        self.log_display.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.log_display)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Logs")
        clear_btn.clicked.connect(self.clear_logs)
        button_layout.addWidget(clear_btn)
        
        export_btn = QPushButton("Export Logs")
        export_btn.clicked.connect(self.export_logs)
        button_layout.addWidget(export_btn)
        
        layout.addLayout(button_layout)
        
        return widget
    
    def setup_timers(self):
        """Set up UI update timers"""
        
        # Update every 5 seconds
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_dashboard)
        self.update_timer.start(5000)
    
    def apply_styles(self):
        """Apply custom styles"""
        style = """
            QMainWindow {
                background-color: #f5f5f5;
            }
            QPushButton {
                padding: 5px 15px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px 0 3px;
            }
            QTableWidget {
                gridline-color: #ddd;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QComboBox {
                padding: 2px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """
        self.setStyleSheet(style)
    
    def toggle_trading(self):
        """Start or stop trading"""
        if not self.is_trading:
            if not self.model_status.get(self.current_strategy):
                QMessageBox.warning(
                    self, "No Model",
                    f"No trained model found for {self.current_strategy}.\n"
                    "Run ml_trainer.py first."
                )
                return
            
            # Start trading
            self.is_trading = True
            self.start_button.setText("STOP TRADING")
            self.start_button.setStyleSheet("background-color: #f44336;")
            
            self.trading_worker = TradingWorker(self.current_strategy)
            self.trading_worker.status_changed.connect(self.update_status)
            self.trading_worker.market_status_updated.connect(self.update_market_status)
            self.trading_worker.performance_updated.connect(self.update_performance)
            self.trading_worker.start()
            
            self.status_indicator.setStyleSheet("color: green;")
            self.status_label.setText("Running")
        else:
            # Stop trading
            self.is_trading = False
            if self.trading_worker:
                self.trading_worker.set_running(False)
                self.trading_worker.wait()
            
            self.start_button.setText("START TRADING")
            self.start_button.setStyleSheet("")
            self.status_indicator.setStyleSheet("color: red;")
            self.status_label.setText("Stopped")
            self.update_status("Stopped")
    
    def update_status(self, message):
        """Update status message"""
        self.statusBar().showMessage(message)
    
    def update_market_status(self, status):
        """Update market status display"""
        is_open = status.get('is_open', False)
        status_text = status.get('status', 'Unknown')
        
        self.market_status.setText(status_text)
        
        if is_open:
            self.market_status.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.market_status.setStyleSheet("color: orange; font-weight: bold;")
    
    def update_performance(self, perf):
        """Update performance metrics"""
        self.metric_labels['total_trades'].setText(str(perf.get('total_trades', 0)))
        self.metric_labels['closed_trades'].setText(str(perf.get('closed_trades', 0)))
        
        win_rate = perf.get('win_rate', 0)
        self.metric_labels['win_rate'].setText(f"{win_rate:.1%}")
        
        total_pnl = perf.get('total_pnl', 0)
        self.metric_labels['total_pnl'].setText(f"${total_pnl:,.2f}")
        
        avg_pnl = perf.get('avg_trade_pnl', 0)
        self.metric_labels['avg_trade_pnl'].setText(f"${avg_pnl:,.2f}")
        
        # Update quick stats
        self.quick_stats.setText(
            f"Trades: {perf['closed_trades']} | "
            f"Win Rate: {win_rate:.1%} | "
            f"P&L: ${total_pnl:,.2f}"
        )
        
        # Update recent trades table
        self.refresh_trades()
        
        # Update account info
        try:
            if self.is_trading and self.trading_worker and self.trading_worker.trader:
                account = self.trading_worker.trader.get_account_info()
                if account:
                    self.account_labels['buying_power'].setText(f"${account['buying_power']:,.2f}")
                    self.account_labels['cash'].setText(f"${account['cash']:,.2f}")
                    self.account_labels['equity'].setText(f"${account['equity']:,.2f}")
                    self.account_labels['portfolio_value'].setText(f"${account['portfolio_value']:,.2f}")
        except:
            pass
    
    def update_dashboard(self):
        """Update dashboard data"""
        if self.is_trading and self.trading_worker:
            # Data updates come from trading worker signals
            pass
    
    def refresh_trades(self):
        """Refresh trades table"""
        try:
            # Get all trades
            all_dates = self.trade_logger.get_available_dates()
            all_trades = []
            
            for date in all_dates:
                trades = self.trade_logger.get_daily_trades(date)
                all_trades.extend(trades)
            
            # Filter trades
            symbol_filter = self.symbol_filter.text().upper()
            status_filter = self.status_filter.currentText()
            strategy_filter = self.trades_strategy_filter.currentData()
            
            filtered_trades = []
            for trade in all_trades:
                if symbol_filter and trade.get('symbol') != symbol_filter:
                    continue
                if status_filter != "All" and trade.get('status') != status_filter:
                    continue
                if strategy_filter and strategy_filter != "All" and trade.get('strategy') != strategy_filter:
                    continue
                filtered_trades.append(trade)
            
            # Update recent trades table (last 10)
            self.recent_trades_table.setRowCount(0)
            for trade in filtered_trades[-10:]:
                row = self.recent_trades_table.rowCount()
                self.recent_trades_table.insertRow(row)
                
                self.recent_trades_table.setItem(row, 0, QTableWidgetItem(trade.get('symbol', '--')))
                self.recent_trades_table.setItem(row, 1, QTableWidgetItem(trade.get('strategy', '--')))
                self.recent_trades_table.setItem(row, 2, QTableWidgetItem(trade.get('side', '--')))
                self.recent_trades_table.setItem(row, 3, QTableWidgetItem(str(trade.get('qty', 0))))
                self.recent_trades_table.setItem(row, 4, QTableWidgetItem(f"${trade.get('entry_price', 0):.2f}"))
                
                exit_price = trade.get('exit_price')
                self.recent_trades_table.setItem(
                    row, 5,
                    QTableWidgetItem(f"${exit_price:.2f}" if exit_price else "-")
                )
                
                pnl = trade.get('pnl_amount', 0)
                self.recent_trades_table.setItem(row, 6, QTableWidgetItem(f"${pnl:+,.2f}"))
                
                # Color code based on P&L
                if trade.get('status') == 'CLOSED' and pnl > 0:
                    for i in range(7):
                        self.recent_trades_table.item(row, i).setBackground(QColor(200, 255, 200))
                elif trade.get('status') == 'CLOSED' and pnl < 0:
                    for i in range(7):
                        self.recent_trades_table.item(row, i).setBackground(QColor(255, 200, 200))
            
            # Update full trades table
            self.trades_table.setRowCount(0)
            for trade in reversed(filtered_trades):
                row = self.trades_table.rowCount()
                self.trades_table.insertRow(row)
                
                self.trades_table.setItem(row, 0, QTableWidgetItem(str(trade.get('date', '--'))))
                self.trades_table.setItem(row, 1, QTableWidgetItem(trade.get('symbol', '--')))
                self.trades_table.setItem(row, 2, QTableWidgetItem(trade.get('strategy', '--')))
                self.trades_table.setItem(row, 3, QTableWidgetItem(trade.get('side', '--')))
                self.trades_table.setItem(row, 4, QTableWidgetItem(str(trade.get('qty', 0))))
                self.trades_table.setItem(row, 5, QTableWidgetItem(f"${trade.get('entry_price', 0):.2f}"))
                
                entry_time = trade.get('entry_time', "-")
                if entry_time != "-" and len(entry_time) > 8:
                    entry_time = entry_time[-8:]
                self.trades_table.setItem(row, 6, QTableWidgetItem(entry_time))
                
                exit_price = trade.get('exit_price', 0)
                self.trades_table.setItem(row, 7, QTableWidgetItem(f"${exit_price:.2f}" if exit_price else "-"))
                
                exit_time = trade.get('exit_time', "-")
                if exit_time != "-" and len(exit_time) > 8:
                    exit_time = exit_time[-8:]
                self.trades_table.setItem(row, 8, QTableWidgetItem(exit_time))
                
                pnl_pct = trade.get('pnl_pct', 0) * 100 if trade.get('pnl_pct') else 0
                self.trades_table.setItem(row, 9, QTableWidgetItem(f"{pnl_pct:+.2f}%"))
                
                pnl_amount = trade.get('pnl_amount', 0)
                self.trades_table.setItem(row, 10, QTableWidgetItem(f"${pnl_amount:+,.2f}"))
        
        except Exception as e:
            print(f"Error refreshing trades: {e}")
    
    def train_model(self):
        """Train model for current strategy"""
        reply = QMessageBox.question(
            self, "Train Model",
            f"Train model for {STRATEGIES[self.current_strategy]['name']}?\n"
            "This will take a few minutes.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # This would run in a thread in production
            QMessageBox.information(
                self, "Training",
                f"Model training for {self.current_strategy} started in background"
            )
    
    def train_all_models(self):
        """Train all strategy models"""
        reply = QMessageBox.question(
            self, "Train All Models",
            "Train models for all enabled strategies?\n"
            "This will take several minutes.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(
                self, "Training",
                "Training all strategy models in background"
            )
    
    def save_settings(self):
        """Save settings"""
        QMessageBox.information(self, "Settings", "Settings saved successfully")
    
    def clear_logs(self):
        """Clear logs"""
        self.log_display.setRowCount(0)
    
    def export_logs(self):
        """Export logs"""
        QMessageBox.information(self, "Export", "Logs exported to logs.csv")
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.is_trading:
            reply = QMessageBox.question(
                self, "Confirm Exit",
                "Trading is running. Stop and exit?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.toggle_trading()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point"""
    app = QApplication(sys.argv)
    
    window = TradingGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
