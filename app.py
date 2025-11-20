from flask import Flask, render_template, request, jsonify
from trading_engine import get_real_time_quote, check_and_execute_trades
from database import init_db, add_trading_rule, get_portfolio, get_transactions, get_active_rules
from apscheduler.schedulers.background import BackgroundScheduler
import json

app = Flask(__name__)

# Initialize database
init_db()

# Start background scheduler for auto-trading
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_execute_trades, trigger="interval", seconds=5)
scheduler.start()

@app.route('/')
def dashboard():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/quote/<symbol>')
def get_quote(symbol):
    """API: Get real-time stock quote"""
    quote = get_real_time_quote(symbol)
    if quote:
        return jsonify(quote)
    return jsonify({'error': 'Symbol not found or invalid'}), 404

@app.route('/api/rules', methods=['POST'])
def create_rule():
    """API: Create new trading rule"""
    data = request.json
    try:
        rule_id = add_trading_rule(
            symbol=data['symbol'],
            rule_type=data['type'],  # 'buy' or 'sell'
            target_price=float(data['targetPrice']),
            quantity=int(data['quantity'])
        )
        return jsonify({'success': True, 'ruleId': rule_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/rules')
def get_rules():
    """API: Get active trading rules"""
    return jsonify(get_active_rules())

@app.route('/api/portfolio')
def get_portfolio_api():
    """API: Get current portfolio"""
    return jsonify(get_portfolio())

@app.route('/api/transactions')
def get_transactions_api():
    """API: Get recent transactions"""
    return jsonify(get_transactions())

if __name__ == '__main__':
    print("🚀 Starting Automated Trading Bot...")
    print("📊 Dashboard: http://localhost:5000")
    app.run(debug=True, use_reloader=False)