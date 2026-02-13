from flask import Flask, render_template, jsonify
from services.data_generator import MarketDataGenerator
from services.ml_predictor import TradingPredictor
from services.trading_engine import TradingEngine

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

market = MarketDataGenerator()
predictor = TradingPredictor()
engine = TradingEngine()

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/tick')
def tick():
    ticks = market.generate_tick()
    current_prices = market.get_all_current()

    predictions = {}
    for symbol in market.symbols:
        history = market.get_history(symbol)
        pred = predictor.predict(history)
        predictions[symbol] = pred

        trade = engine.execute_signal(symbol, pred["signal"], market.current_prices[symbol], pred["confidence"])

    portfolio = engine.get_portfolio_value(current_prices)
    trades = engine.get_recent_trades()

    return jsonify({
        "ticks": ticks,
        "predictions": predictions,
        "portfolio": portfolio,
        "trades": trades
    })

@app.route('/api/history/<symbol>')
def history(symbol):
    data = market.get_history(symbol)
    pred = predictor.predict(data)
    return jsonify({"history": data, "prediction": pred})

@app.route('/api/portfolio')
def portfolio():
    current_prices = market.get_all_current()
    return jsonify(engine.get_portfolio_value(current_prices))

@app.route('/api/pnl')
def pnl():
    return jsonify({"pnl_history": engine.get_pnl_history()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
