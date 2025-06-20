from flask import Flask, render_template, request, redirect, url_for, flash
from bot import BasicBot
import os
import json
from binance.exceptions import BinanceAPIException
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecretkey')
ORDERS_FILE = 'orders.json'

def save_order_to_history(order_data):
    try:
        if os.path.exists(ORDERS_FILE):
            with open(ORDERS_FILE, 'r') as f:
                orders = json.load(f)
        else:
            orders = []
        orders.append(order_data)
        with open(ORDERS_FILE, 'w') as f:
            json.dump(orders, f, indent=2)
    except Exception as e:
        print(f"Error saving order: {e}")

def load_order_history():
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r') as f:
            return json.load(f)
    return []

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    if request.method == 'POST':
        api_key = request.form.get('api_key')
        api_secret = request.form.get('api_secret')
        order_type = request.form.get('order_type')
        symbol = request.form.get('symbol')
        side = request.form.get('side')
        try:
            bot = BasicBot(api_key, api_secret)
            order_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            if order_type == 'market':
                quantity = float(request.form.get('quantity'))
                order = bot.place_market_order(symbol, side, quantity)
            elif order_type == 'limit':
                quantity = float(request.form.get('quantity'))
                price = float(request.form.get('price'))
                order = bot.place_limit_order(symbol, side, quantity, price)
            elif order_type == 'stop-limit':
                quantity = float(request.form.get('quantity'))
                price = float(request.form.get('price'))
                stop_price = float(request.form.get('stop_price'))
                order = bot.place_stop_limit_order(symbol, side, quantity, price, stop_price)
            elif order_type == 'twap':
                total_quantity = float(request.form.get('total_quantity'))
                slices = int(request.form.get('slices'))
                interval_sec = int(request.form.get('interval_sec'))
                order = bot.place_twap_order(symbol, side, total_quantity, slices, interval_sec)
            else:
                order = None
            if order:
                if isinstance(order, dict):
                    result = json.dumps(order, indent=2)
                else:
                    result = str(order)
                save_order_to_history({
                    'time': order_time,
                    'type': order_type,
                    'symbol': symbol,
                    'side': side,
                    'result': result
                })
            else:
                error = 'Order could not be placed. Please check your input and try again.'
        except BinanceAPIException as e:
            error = f"Binance API Error: {e.message} (Code: {e.code})"
        except Exception as e:
            if 'API-key format invalid' in str(e) or 'API-key, API-secret' in str(e):
                error = 'Order could not be placed. Wrong credentials.'
            else:
                error = f"Error: {e}"
    return render_template('index.html', result=result, error=error)

@app.route('/history')
def history():
    orders = load_order_history()
    return render_template('history.html', orders=orders)

if __name__ == '__main__':
    app.run(debug=True) 