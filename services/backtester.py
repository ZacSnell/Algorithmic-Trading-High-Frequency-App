# services/backtester.py
from config import *
from ml_ensemble import EnsembleCoordinator
from ml_specialist import Specialist
from build_dataset import add_features_and_target, download_intraday
import pandas as pd
import matplotlib.pyplot as plt
import os

class Backtester:
    def __init__(self):
        self.ensemble = EnsembleCoordinator()
        self.agent_stats = {name: {'correct': 0, 'total': 0, 'pnl_contrib': 0.0} for name in SPECIALISTS}

    def run_backtest(self, symbols=None):
        if symbols is None:
            symbols = ["SPY"]
        for symbol in symbols:
            logger.info(f"\n🚀 Running backtest on {symbol}...")
            df = download_intraday(symbol, strategy='macd_crossover')
            if df is None or len(df) < 100:
                continue
            df = add_features_and_target(df)

            equity = 100_000.0
            position = 0
            entry_price = 0
            equity_curve = [equity]
            trades = []

            for i in range(50, len(df) - LOOKAHEAD_BARS):
                current_df = df.iloc[:i+1].copy()
                result = self.ensemble.predict(current_df, symbol)

                # Show News Catalyst vote explicitly
                news_vote = self.ensemble.news_agent.predict([symbol])
                logger.info(f"  News Catalyst → Signal: {news_vote['signal']} | Conf: {news_vote['confidence']:.1%} | {news_vote['rationale']}")

                price = current_df['Close'].iloc[-1]
                future_price = df['Close'].iloc[i + LOOKAHEAD_BARS]
                actual_return = (future_price / price) - 1
                actual_signal = 1 if actual_return > PROFIT_THRESHOLD * 0.5 else 0

                for name, agent in self.ensemble.specialists.items():
                    if isinstance(agent, Specialist):
                        pred = agent.predict(current_df)
                        self.agent_stats[name]['total'] += 1
                        if pred['signal'] == actual_signal:
                            self.agent_stats[name]['correct'] += 1
                        self.agent_stats[name]['pnl_contrib'] += pred['confidence'] * actual_return * 5000

                # Trade logic
                if result['recommendation'] == "BUY" and position == 0:
                    position = int(equity * (POSITION_SIZE_PCT / 100.0) / price)
                    entry_price = price
                    trades.append({'entry_time': current_df.index[-1], 'entry_price': entry_price, 'qty': position})
                elif position > 0 and (result['recommendation'] == "HOLD" or actual_return < -STOP_LOSS_PCT):
                    pnl = position * (price - entry_price)
                    equity += pnl
                    equity_curve.append(equity)
                    trades[-1].update({'exit_time': current_df.index[-1], 'exit_price': price, 'pnl': pnl})
                    position = 0
                else:
                    equity_curve.append(equity)

            if position > 0:
                pnl = position * (df['Close'].iloc[-1] - entry_price)
                equity += pnl

            win_rate = len([t for t in trades if t.get('pnl', 0) > 0]) / len(trades) * 100 if trades else 0
            total_pnl = equity - 100_000

            logger.info(f"\n{'='*70}")
            logger.info(f"BACKTEST COMPLETE — {symbol}")
            logger.info(f"Final Equity: ${equity:,.2f} | P&L: ${total_pnl:,.2f}")
            logger.info(f"Win Rate: {win_rate:.1f}% | Trades: {len(trades)}")
            logger.info(f"{'='*70}")

            print("\n📊 AGENT PERFORMANCE")
            for name, stats in self.agent_stats.items():
                acc = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
                print(f"  {SPECIALISTS[name]['name']:22} | Accuracy: {acc:5.1f}% | P&L contrib: ${stats['pnl_contrib']:,.0f}")

            os.makedirs("models/backtest_results", exist_ok=True)
            pd.DataFrame(trades).to_csv(f"models/backtest_results/{symbol}_trades.csv", index=False)
            plt.figure(figsize=(12,6))
            plt.plot(equity_curve, label='Equity', color='blue')
            plt.title(f'Equity Curve — {symbol}')
            plt.legend()
            plt.grid(True)
            plt.savefig(f"models/backtest_results/{symbol}_equity_curve.png")
            plt.close()

if __name__ == "__main__":
    bt = Backtester()
    bt.run_backtest(symbols=["SPY"])