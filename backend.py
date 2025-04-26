from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd

app = Flask(__name__)
CORS(app)

# In-memory portfolio
portfolio = {}

@app.route('/api/stock/<ticker>', methods=['GET'])
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if data.empty or "Close" not in data:
            return jsonify({"error": f"No data found for {ticker}"}), 404

        last_price = data["Close"].iloc[-1]
        return jsonify({
            "ticker": ticker,
            "price": float(last_price),
            "timestamp": pd.Timestamp.now().isoformat()
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio', methods=['POST'])
def add_to_portfolio():
    try:
        data = request.json
        ticker = data.get("ticker", "").upper()
        quantity = int(data.get("quantity", 0))
        buy_price = float(data.get("buy_price", 0))

        if not ticker or quantity <= 0 or buy_price <= 0:
            return jsonify({"error": "Invalid data"}), 400

        if ticker in portfolio:
            portfolio[ticker]["quantity"] += quantity
            portfolio[ticker]["total_cost"] += quantity * buy_price
        else:
            portfolio[ticker] = {"quantity": quantity, "total_cost": quantity * buy_price}

        return jsonify({"message": f"{ticker} added", "portfolio": portfolio})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    try:
        if not portfolio:
            return jsonify({"message": "Portfolio is empty", "portfolio": {}, "total_value": 0})

        portfolio_data = {}
        total_value = 0

        for ticker, data in portfolio.items():
            stock = yf.Ticker(ticker)
            history = stock.history(period="1d")
            if history.empty or "Close" not in history:
                continue

            price = history["Close"].iloc[-1]
            value = price * data["quantity"]
            gain_loss = value - data["total_cost"]
            portfolio_data[ticker] = {
                "quantity": data["quantity"],
                "buy_price": round(data["total_cost"] / data["quantity"], 2),
                "current_price": round(price, 2),
                "current_value": round(value, 2),
                "gain_loss": round(gain_loss, 2)
            }
            total_value += value

        return jsonify({"portfolio": portfolio_data, "total_value": round(total_value, 2)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/<ticker>', methods=['DELETE'])
def remove_from_portfolio(ticker):
    try:
        ticker = ticker.upper()
        if ticker in portfolio:
            del portfolio[ticker]
            return jsonify({"message": f"{ticker} removed"})
        return jsonify({"error": f"{ticker} not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
