# trade_logger.py
# Comprehensive trade logging system with daily organization and historical lookup
# Tracks all trades by day for analysis and backtesting

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from config import *
import json
from datetime import datetime, timedelta


class TradeLogger:
    """
    Logs all trades with strategy, entry/exit, P&L, and metadata.
    Organizes trades by date for easy historical lookup.
    """
    
    def __init__(self):
        self.logs_dir = LOGS_DIR
        self.strategy_logs_dir = STRATEGY_LOGS_DIR
        self.today = datetime.now(tz=TIMEZONE).date()
        self.current_day_log = self.get_today_log()
    
    def get_log_filename(self, date=None):
        """Get the log filename for a specific date (YYYY-MM-DD format)"""
        if date is None:
            date = self.today
        
        if isinstance(date, str):
            return f"{date}_trades.json"
        return f"{date.strftime('%Y-%m-%d')}_trades.json"
    
    def get_strategy_log_filename(self, strategy, date=None):
        """Get strategy-specific log filename"""
        if date is None:
            date = self.today
        
        if isinstance(date, str):
            return f"{strategy}_{date}_trades.json"
        return f"{strategy}_{date.strftime('%Y-%m-%d')}_trades.json"
    
    def get_today_log(self):
        """Get path to today's trade log"""
        return self.logs_dir / self.get_log_filename()
    
    def get_strategy_today_log(self, strategy):
        """Get path to today's strategy-specific log"""
        return self.strategy_logs_dir / self.get_strategy_log_filename(strategy)
    
    def log_trade(self, trade_data, strategy='macd_crossover'):
        """
        Log a single trade to both daily and strategy-specific logs
        
        trade_data: {
            'symbol': 'AAPL',
            'strategy': 'macd_crossover',
            'side': 'BUY' or 'SELL',
            'qty': 10,
            'entry_price': 150.25,
            'entry_time': datetime,
            'exit_price': 151.00,  # Optional
            'exit_time': datetime,  # Optional
            'pnl_amount': 7.50,  # Optional
            'pnl_pct': 0.005,  # Optional
            'status': 'OPEN' or 'CLOSED',
            'reason': 'MACD crossup',
            'confidence': 0.75,
            'order_id': 'abc123'
        }
        """
        try:
            # Ensure timestamp format
            if isinstance(trade_data.get('entry_time'), datetime):
                trade_data['entry_time'] = trade_data['entry_time'].isoformat()
            
            if trade_data.get('exit_time') and isinstance(trade_data.get('exit_time'), datetime):
                trade_data['exit_time'] = trade_data['exit_time'].isoformat()
            
            # Add timestamp if not present
            if 'timestamp' not in trade_data:
                trade_data['timestamp'] = datetime.now(tz=TIMEZONE).isoformat()
            
            # Log to daily log
            self._append_to_log(self.get_today_log(), trade_data)
            
            # Log to strategy-specific log
            self._append_to_log(
                self.get_strategy_today_log(strategy),
                trade_data
            )
            
            logger.info(f"Trade logged: {trade_data['symbol']} {trade_data['side']} @ {trade_data['entry_price']}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log trade: {e}")
            return False
    
    def _append_to_log(self, log_path, trade_data):
        """Append trade to a JSON log file"""
        try:
            # Load existing trades
            if log_path.exists():
                with open(log_path, 'r') as f:
                    data = json.load(f)
                    trades = data.get('trades', [])
            else:
                trades = []
            
            # Append new trade
            trades.append(trade_data)
            
            # Save updated log
            log_data = {
                'date': str(self.today),
                'total_trades': len(trades),
                'trades': trades
            }
            
            with open(log_path, 'w') as f:
                json.dump(log_data, f, indent=2)
        
        except Exception as e:
            logger.error(f"Error appending to log {log_path}: {e}")
    
    def get_daily_trades(self, date=None):
        """Retrieve all trades for a specific date"""
        if date is None:
            date = self.today
        
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        log_path = self.logs_dir / self.get_log_filename(date)
        
        if not log_path.exists():
            return {
                'date': str(date),
                'total_trades': 0,
                'trades': []
            }
        
        try:
            with open(log_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read trades for {date}: {e}")
            return {'date': str(date), 'total_trades': 0, 'trades': []}
    
    def get_strategy_daily_trades(self, strategy, date=None):
        """Retrieve trades for a specific strategy on a specific date"""
        if date is None:
            date = self.today
        
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        
        log_path = self.strategy_logs_dir / self.get_strategy_log_filename(strategy, date)
        
        if not log_path.exists():
            return {
                'strategy': strategy,
                'date': str(date),
                'total_trades': 0,
                'trades': []
            }
        
        try:
            with open(log_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read {strategy} trades for {date}: {e}")
            return {'strategy': strategy, 'date': str(date), 'total_trades': 0, 'trades': []}
    
    def get_date_range_trades(self, start_date, end_date=None):
        """Get all trades in a date range"""
        if end_date is None:
            end_date = self.today
        
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        all_trades = []
        current = start_date
        
        while current <= end_date:
            daily_data = self.get_daily_trades(current)
            all_trades.extend(daily_data.get('trades', []))
            current += timedelta(days=1)
        
        return {
            'start_date': str(start_date),
            'end_date': str(end_date),
            'total_trades': len(all_trades),
            'trades': all_trades
        }
    
    def get_available_dates(self):
        """Get list of dates with trade logs"""
        dates = []
        
        for log_file in sorted(self.logs_dir.glob('*_trades.json')):
            try:
                # Extract date from filename (YYYY-MM-DD format)
                date_str = log_file.stem.replace('_trades', '')
                dates.append(date_str)
            except:
                pass
        
        return sorted(dates, reverse=True)  # Most recent first
    
    def get_daily_statistics(self, date=None):
        """Calculate statistics for a specific day"""
        if date is None:
            date = self.today
        
        data = self.get_daily_trades(date)
        trades = data.get('trades', [])
        
        if not trades:
            return {
                'date': str(date),
                'total_trades': 0,
                'closed_trades': 0,
                'open_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'win_rate': 0,
                'best_trade': None,
                'worst_trade': None
            }
        
        closed_trades = [t for t in trades if t.get('status') == 'CLOSED']
        winning = [t for t in closed_trades if t.get('pnl_amount', 0) > 0]
        losing = [t for t in closed_trades if t.get('pnl_amount', 0) < 0]
        
        total_pnl = sum(t.get('pnl_amount', 0) for t in closed_trades)
        
        return {
            'date': str(date),
            'total_trades': len(trades),
            'closed_trades': len(closed_trades),
            'open_trades': len([t for t in trades if t.get('status') == 'OPEN']),
            'winning_trades': len(winning),
            'losing_trades': len(losing),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl': round(total_pnl / len(closed_trades), 2) if closed_trades else 0,
            'win_rate': round(len(winning) / len(closed_trades) * 100, 2) if closed_trades else 0,
            'best_trade': max(closed_trades, key=lambda t: t.get('pnl_amount', 0)) if closed_trades else None,
            'worst_trade': min(closed_trades, key=lambda t: t.get('pnl_amount', 0)) if closed_trades else None
        }
    
    def get_strategy_statistics(self, strategy, date=None):
        """Calculate statistics for a specific strategy on a specific day"""
        if date is None:
            date = self.today
        
        data = self.get_strategy_daily_trades(strategy, date)
        trades = data.get('trades', [])
        
        if not trades:
            return {
                'strategy': strategy,
                'date': str(date),
                'total_trades': 0,
                'total_pnl': 0,
                'avg_pnl': 0,
                'win_rate': 0
            }
        
        closed_trades = [t for t in trades if t.get('status') == 'CLOSED']
        winning = [t for t in closed_trades if t.get('pnl_amount', 0) > 0]
        
        total_pnl = sum(t.get('pnl_amount', 0) for t in closed_trades)
        
        return {
            'strategy': strategy,
            'date': str(date),
            'total_trades': len(trades),
            'closed_trades': len(closed_trades),
            'winning_trades': len(winning),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl': round(total_pnl / len(closed_trades), 2) if closed_trades else 0,
            'win_rate': round(len(winning) / len(closed_trades) * 100, 2) if closed_trades else 0
        }
    
    def update_trade(self, trade_id, updates, date=None):
        """Update an existing trade (e.g., close it with exit price)"""
        if date is None:
            date = self.today
        
        log_path = self.logs_dir / self.get_log_filename(date)
        
        if not log_path.exists():
            logger.warning(f"No trades found for {date}")
            return False
        
        try:
            with open(log_path, 'r') as f:
                data = json.load(f)
            
            # Find and update trade by order_id or index
            for trade in data.get('trades', []):
                if trade.get('order_id') == trade_id or trade.get('id') == trade_id:
                    trade.update(updates)
                    
                    with open(log_path, 'w') as f:
                        json.dump(data, f, indent=2)
                    
                    logger.info(f"Updated trade {trade_id}")
                    return True
            
            logger.warning(f"Trade {trade_id} not found in {date} logs")
            return False
        
        except Exception as e:
            logger.error(f"Error updating trade: {e}")
            return False
    
    def export_csv(self, start_date, end_date=None, filename=None):
        """Export trades to CSV for analysis"""
        if filename is None:
            filename = f"trades_{start_date}_to_{end_date or self.today}.csv"
        
        import csv
        csv_path = self.logs_dir / filename
        
        trades_data = self.get_date_range_trades(start_date, end_date)
        trades = trades_data.get('trades', [])
        
        if not trades:
            logger.warning("No trades to export")
            return None
        
        try:
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=trades[0].keys())
                writer.writeheader()
                writer.writerows(trades)
            
            logger.info(f"Exported {len(trades)} trades to {csv_path}")
            return csv_path
        
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return None
    
    def export_daily_trades_to_csv(self, date_str):
        """Export trades from a specific day to CSV file"""
        import csv
        
        try:
            # Parse date string if needed
            if isinstance(date_str, str):
                date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date_obj = date_str
            
            # Get trades for that specific day
            trades = self.get_daily_trades(date_obj)
            
            if not trades:
                logger.warning(f"No trades found for {date_obj}")
                return None
            
            # Create CSV filename
            csv_filename = f"trades_{date_obj.strftime('%Y-%m-%d')}.csv"
            csv_path = self.logs_dir / csv_filename
            
            # Write to CSV
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=trades[0].keys())
                writer.writeheader()
                writer.writerows(trades)
            
            logger.info(f"Exported {len(trades)} trades for {date_obj} to {csv_path}")
            return str(csv_path)
        
        except Exception as e:
            logger.error(f"Error exporting daily trades: {e}")
            return None


# Global instance
trade_logger = TradeLogger()
