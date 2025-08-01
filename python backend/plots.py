import yfinance as yf
import requests
import sqlite3
import matplotlib.pyplot as plt
from datetime import date
from flask import Flask, request, jsonify
import pandas as pd
import plotly.graph_objects as go
from flask_cors import CORS
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold  
import numpy as np
import pandas as pd


app = Flask(__name__)

CORS(app)

def connection():
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(""" CREATE TABLE IF NOT EXISTS Users(
                   Sno INTEGER PRIMARY KEY AUTOINCREMENT,
                   Username TEXT NOT NULL UNIQUE,
                   Password TEXT NOT NULL UNIQUE,
                   Email TEXT NOT NULL UNIQUE
                   )
""")
    
    conn.commit()
    conn.close()

connection()


def connection2():
    conn = sqlite3.connect('stock.db')
    cursor = conn.cursor()
    cursor.execute(""" CREATE TABLE IF NOT EXISTS Stocks (
                   StockID INTEGER PRIMARY KEY AUTOINCREMENT,
                   Username TEXT NOT NULL,
                   StockName TEXT NOT NULL,
                   Quantity INTEGER NOT NULL,
                   Price_per_share REAL NOT NULL,
                   Date DATE DEFAULT CURRENT_DATE,
                   ticker_symbol TEXT NOT NULL
                   )
""")
    
    conn.commit()
    conn.close()

connection2()

@app.route('/add_stock', methods=['POST'])
def add_stock():
    try:
        data = request.get_json()
        username = data['username']
        stock_name = data['stock_name']
        quantity = int(data['quantity'])
        price_per_share = float(data['price_per_share'])
        date_actual = data.get('date', date.today().strftime("%Y-%m-%d"))

        ticker_symbol = search_ticker(stock_name)

        # Store in DB
        conn = sqlite3.connect('stock.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO Stocks (Username, StockName, Quantity, Price_per_share, Date, ticker_symbol)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, stock_name, quantity, price_per_share, date_actual, ticker_symbol))
        conn.commit()
        conn.close()

        # Prepare response
        temp = [stock_name, quantity, price_per_share, date_actual]

        live_price = get_live_price(ticker_symbol)
        temp.append(live_price)
        temp.append((live_price - price_per_share) * quantity)

        # Get percentage change
        try:
            ticker = yf.Ticker(ticker_symbol)
            hist_data = ticker.history(period="2d", interval="1d")

            if not hist_data.empty and len(hist_data["Close"]) >= 2:
                latest = hist_data["Close"].iloc[-1]
                second_latest = hist_data["Close"].iloc[-2]
                pct_change = ((latest - second_latest) / second_latest) * 100
                temp.append(f"{pct_change:.2f}%")
            else:
                temp.append("0.00%")  # Fallback
        except Exception as err:
            temp.append("0.00%")  # Safe fallback

        return jsonify(temp), 201

    except Exception as e:
        return jsonify({"error": "Something went wrong", "details": str(e)}), 500


@ app.route("/register",methods = ['POST'])

def register():
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']
        email = data['email']

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Users(Username, Password, Email) VALUES (?,?,?)",(username,password,email))

        conn.commit()
        conn.close()

        return "registration successful", 201

    except sqlite3.IntegrityError:
        return "User already exists", 400
    except Exception as e: 
        print("Error during registration:", e)
        return "An error occurred", 500
    
@ app.route("/login",methods = ['POST'])
def login():
    try:
        data = request.get_json()
        username = data['username']
        password = data['password']

        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Users WHERE Username=? AND Password=?", (username, password))
        user = cursor.fetchone()

        conn.close()

        if user:
            return jsonify({"status": "Login successful"}), 200
        else:
            return jsonify({"status": "Invalid credentials"}), 401

    except Exception as e:
        return jsonify({"status": "An error occurred"}), 500

def search_ticker(company_name):
    API_KEY = "cImJHzsIgHTcT9OrLdHazXt1u9tvPdJa"
    url = "https://financialmodelingprep.com/api/v3/search"
    params = {
        "query": company_name,
        "limit": 10,
        "apikey": API_KEY
    }
    response = requests.get(url, params=params)
    
    try:
        data = response.json()
    except Exception as e:
        print("Failed to parse JSON:", e)
        return None

    if not data:
        print("No results found for", company_name)
        return None
    
    return data[0].get("symbol")  # return the top match

def get_live_price(ticker_symbol):
    ticker = yf.Ticker(ticker_symbol)
    data = ticker.history(period="1d", interval="1m")
    if not data.empty:
        latest_price = data["Close"].iloc[-1]
        return latest_price
    return None

# plotting our data
@app.route('/plot_live_price', methods=['POST'])
def plot_live_price():

    data = request.get_json()
    stock_name = data.get('stock_name')

    # ticker_symbols = search_ticker(stock_name)
    ticker_symbols = search_ticker(stock_name)  # Hardcoded for Reliance Industries Limited

    today = date.today().strftime("%Y-%m-%d")
    start_date = data.get('start_date', today)
    end_date = data.get('end_date', today)

    data_stock = yf.download(ticker_symbols, start=start_date, end=end_date)
    
    fig = go.Figure()

    # Handle both single and multiple ticker symbols
    fig.add_trace(go.Scatter(
        x=data_stock.index,
        y=data_stock['Close'][ticker_symbols].tolist(),
        mode='lines',
        name=ticker_symbols + " Closing Price",
        line=dict(width=2,color = "royalblue"),
        yaxis = 'y1'
    ))
    fig.add_trace(go.Bar(
        x = data_stock.index,
        y = data_stock['Volume'][ticker_symbols].tolist(),
        name = "Volume",
        marker_color = 'mediumseagreen',
        yaxis = 'y2',
        opacity = 0.4
    ))

    # Customize layout
    fig.update_layout(
    title=f'{ticker_symbols} - Price and Volume Chart',
    xaxis=dict(title='Date'),
    yaxis=dict(
        title='Closing Price (INR)',
        side='left'
    ),
    yaxis2=dict(
        title='Volume',
        overlaying='y',
        side='right',
        showgrid=False
    ),
    legend=dict(x=0.01, y=0.99),
    template='plotly_white',
    height=600
)

    # Save as HTML (for JavaFX WebView)
    fig.write_html("C:/Users/varun/OneDrive/Desktop/java_project/live_stock_prices.html")
    return '', 204  # 204 No Content (valid, and no browser popup)


def plot_profit_loss(username):
    conn = sqlite3.connect("stock.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Stocks WHERE Username=?", (username,))
    stocks = cursor.fetchall()
    stock_dict = {}
    for stock in stocks:
        stock_name = stock[2]
        ticker_symbol = stock[6]
        live_price = get_live_price(ticker_symbol)
        if live_price is not None:
            if stock_name not in stock_dict:
                stock_dict[stock_name] = 0
            stock_dict[stock_name] += (live_price - stock[4]) * stock[3]

    conn.close()

    fig = go.Figure(data=[go.Bar(
        x=list(stock_dict.keys()),
        y=list(stock_dict.values()),
        marker_color='indianred'
    )])
    fig.update_layout(
        title="Profit/Loss for Stocks Owned by " + username,
        xaxis_title="Stocks",
        yaxis_title="Profit/Loss (INR)",
        template="plotly_white"
    )

    fig.write_html("C:/Users/varun/OneDrive/Desktop/java_project/profit_loss.html")


def portfolio_value(username,start_date=None, end_date=None):
    conn = sqlite3.connect("stock.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Stocks WHERE username=?", (username,))
    stocks = cursor.fetchall()

    ticker_symbols = {}
    unique_stocks = {}


    for stock in stocks:
        if stock[2] not in unique_stocks:
            unique_stocks[stock[2]] = 0
        unique_stocks[stock[2]] += stock[3]
        if stock[6] not in ticker_symbols:
            ticker_symbols[stock[2]] = stock[6]


    data = yf.download(list(ticker_symbols.values()), start = start_date,end = end_date )['Close']

    total_value = {}
    for date,row in data.iterrows():
        for stock in unique_stocks:
            ticker_symbol = ticker_symbols[stock]
            if ticker_symbol is not None and ticker_symbol in row:
                if date not in total_value:
                    total_value[date] = 0
                total_value[date] += row[ticker_symbol] * unique_stocks[stock]

    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(total_value.keys()),
        y=list(total_value.values()),
        mode='lines+markers',
        name='Portfolio Value'
    ))
    fig.update_layout(
        title="Portfolio Value Over Time for " + username,
        xaxis_title="Date",
        yaxis_title="Portfolio Value (INR)",
        template="plotly_white"
    )
    fig.write_html("C:/Users/varun/OneDrive/Desktop/java_project/portfolio_value.html")


    conn.close()

@app.route('/portfolio_value_today', methods=['POST'])
def portfolio_value_today():
    try:
        data = request.get_json()
        username = data['username']

        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Stocks WHERE username=?", (username,))
        stocks = cursor.fetchall()

        unique_stocks = {}
        ticker_symbols = {}

        total_value = 0

        for stock in stocks:
            if stock[2] not in unique_stocks:
                unique_stocks[stock[2]] = 0
            unique_stocks[stock[2]] += stock[3]
            ticker_symbols[stock[2]] = stock[6]  # ticker_symbol is now stored in the 6th column

        for stock in unique_stocks:
            ticker_symbol = ticker_symbols[stock]
            if ticker_symbol is not None:
                total_value += get_live_price(ticker_symbol) * unique_stocks[stock]
        
        
        
        return str(f"{total_value:.2f}"),200
    
    except Exception as e:
        return str(e), 500


@app.route('/profit_loss_value', methods=['POST'])
def profit_loss_value():
    try:
        data = request.get_json()
        username = data['username']

        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Stocks WHERE username=?", (username,))
        stocks = cursor.fetchall()

        total = 0
        for stock in stocks:
            # stock_name = stock[2]
            ticker_symbol = stock[6]  # ticker_symbol is now stored in the 6th column
            live_price = get_live_price(ticker_symbol)
            if live_price is not None:
                total += (live_price - stock[4]) * stock[3]
        return str(f"{total:.2f}"), 200
    except Exception as e:
        return str(e), 500
    
@app.route('/investment_value', methods=['POST'])
def investment_value():
    try:
        data = request.get_json()
        username = data['username']
        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Stocks WHERE Username=?", (username,))
        stocks = cursor.fetchall()

        total_investment = 0
        for stock in stocks:
            total_investment += stock[3] * stock[4]  # Quantity * Price_per_share
        return str(f"{total_investment:.2f}"), 200
    
    except Exception as e:
        return str(e), 500
    
    conn.close()

@app.route('/exchange_rate', methods=['POST'])
def exchange_rate():
    try:
        API_KEY = "7eacc4a1b04c26d0169384a9"
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/codes"
        response = requests.get(url)
        data = response.json()

        codes = []
        if data['result'] == 'success':
            code_map = {item[1]: item[0] for item in data['supported_codes']}
            # Sort by currency name (the keys)
            sorted_code_map = dict(sorted(code_map.items()))
            return jsonify(sorted_code_map), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/exchange_rate_value', methods=['POST'])
def exchange_rate_value():
    try:
        data = request.get_json()
        base_currency = data['base_currency']
        target_currency = data['target_currency']

        API_KEY = "7eacc4a1b04c26d0169384a9"
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/pair/{base_currency}/{target_currency}"
        response = requests.get(url)
        result = response.json()
        if result['result'] == 'success':
            return str(result['conversion_rate'])
        
    except Exception as e:
        return None


@app.route('/get_stock_data', methods=['POST'])
def get_stock_data():
    try:
        data = request.get_json()
        username = data['username']
        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Stocks WHERE Username=?", (username,))
        stocks = cursor.fetchall()
        final_stocks = []
        for stock in stocks:
            temp =[]
            temp.append(stock[2])
            temp.append(stock[3])
            temp.append(stock[4])
            temp.append(stock[5])
            ticker_symbol = stock[6]
            if ticker_symbol is not None:
                live_price = get_live_price(ticker_symbol)
                if live_price is not None:
                    temp.append(live_price)
                    temp.append((live_price - stock[4]) * stock[3])
            
            ticker = yf.Ticker(ticker_symbol)
            data = ticker.history(period="2d", interval="1m")
            if not data.empty:
                latest_price = data["Close"].iloc[-1]
                second_latest_price = data["Close"].iloc[-2]
                percantage_change = "%"
                percantage_change += str((latest_price - second_latest_price) / second_latest_price * 100)

                temp.append(percantage_change)
            else:
                temp.append("0.00%")
            final_stocks.append(temp)

        return jsonify(final_stocks), 200
    except Exception as e:
        return None
    conn.close()

@app.route('/detailed_stock_data', methods=['POST'])
def detailed_stock_data():
    try:
        data = request.get_json()
        stock_name = data['stock_name']
        # ticker_symbol = search_ticker(stock_name)
        ticker_symbol = search_ticker(stock_name)  # Hardcoded for Reliance Industries Limited
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        if info:
            stock_data = {
                "symbol": info.get("symbol"),
                "exchange": info.get("exchange"),
                "name": info.get("longName"),
                "industry": info.get("industry"),
                "currentPrice": f"{info.get('currentPrice'):.2f}",
                "previousClose": info.get("regularMarketPreviousClose"),
                "open": info.get("regularMarketOpen"),
                "high": info.get("regularMarketDayHigh"),
                "low": info.get("regularMarketDayLow"),
                "Pe_ratio": info.get("trailingPE"),
                "EPS": info.get("trailingEps"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "bookValue": info.get("bookValue"),
                "200avg":info.get("twoHundredDayAverage")
            }
            return jsonify(stock_data), 200
        
        else:
            return jsonify({"error": "No data found for the stock"}), 404
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/plot_all_graphs', methods=['POST'])
def plot_all_graphs():
    data = request.get_json()
    username = data.get('username')
    stock_name = data.get('stock_name')
    mode = data.get("mode")
    # ticker_symbol = search_ticker(stock_name)
    ticker_symbol = "RELIANCE.NS"  # Hardcoded for Reliance Industries Limited

    if mode == "daily":
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        candle_stick_graph(stock_name,ticker_symbol,start_date, end_date)
        plot_profit_loss(username)
        portfolio_value(username)
    
    elif mode == "monthly":
        month = data.get('month')
        year = data.get('year')
        start_date = f"{year}-{month}-01"
        end_date = f"{year}-{month}-28"  # Assuming 28 days for
        candle_stick_graph(stock_name,ticker_symbol,start_date, end_date)
        plot_profit_loss(username)
        portfolio_value(username)
    
    elif mode == "yearly":
        year = data.get('year')
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        candle_stick_graph(stock_name,ticker_symbol,start_date, end_date)
        plot_profit_loss(username)
        portfolio_value(username)
    
    return '',204

def candle_stick_graph(stock_name,ticker_symbol, start_date, end_date):
    data = yf.download(ticker_symbol, start=start_date, end=end_date)
    print(data['Open'][ticker_symbol].tolist())
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                                         open=data['Open'][ticker_symbol].tolist(),
                                         high=data['High'][ticker_symbol].tolist(),
                                         low=data['Low'][ticker_symbol].tolist(),
                                         close=data['Close'][ticker_symbol].tolist())])
    fig.update_layout(
        title=f"Candlestick Chart for {stock_name}",
        xaxis_title="Date",
        yaxis_title="Price (INR)",
        template="plotly_white"
    )
    fig.write_html("C:/Users/varun/OneDrive/Desktop/java_project/candlestick_chart.html")

def get_prediction(stock_name):
    ticker_symbol = search_ticker(stock_name)

    ticker = yf.Ticker(ticker_symbol)
    df = ticker.history(period='2y')

    df.reset_index(inplace=True)
    df['Date'] = df['Date'].astype(str)

    df["Result"] = df["Close"].pct_change()
    df["Result"] = df["Result"].fillna(0)
    df['M_10'] = df['Close'].rolling(window=10).mean()
    df['M_50'] = df['Close'].rolling(window=50).mean()
    df['volatility'] = df['Close'].rolling(window=10).std()
    df['volatility'] = df['volatility'].fillna(0)
    df['Momentum'] = df['Close'].diff(10)

    # target value will be binary whether the price will go up or down after 30 days
    df['Target'] = (df['Close'].shift(-30) > df['Close']).astype(int)
    df = df.dropna()
    df = df[['Result', 'M_10', 'M_50', 'volatility', 'Momentum', 'Target']]
    x = df.drop(columns=['Target'])
    y = df['Target']
        # Define hyperparameter grid for Random Forest
    n_estimators = [200,300,500]
    max_features = ['sqrt', 'log2']
    max_depth = [3, 5]
    max_depth.append(None)
    min_samples_split = [2, 5]
    min_samples_leaf = [2, 4, 5]
    bootstrap = [True, False]
    params_grid = {'n_estimators': n_estimators, 'max_features': max_features,
                'max_depth': max_depth, 'min_samples_split': min_samples_split,
                'min_samples_leaf': min_samples_leaf, 'bootstrap': bootstrap}

    # Initialize and run GridSearchCV for Random Forest
    skfold = StratifiedKFold(n_splits=5,shuffle=True,random_state=42)
    rf_clf = RandomForestClassifier(random_state=42)
    rf_cv = GridSearchCV(rf_clf, params_grid, scoring="accuracy", cv=skfold, verbose=2, n_jobs=-1)
    rf_cv.fit(x,y)
    best_params = rf_cv.best_params_
    # Display best parameters and cross-validation accuracy
    print(f"Best parameters: {best_params}")
    print("Accuracy for Random Forest:", rf_cv.best_score_)
    # Get the best Random Forest model
    best_rf_model = rf_cv.best_estimator_

    latest = x.iloc[-1].to_frame().T
    probability = best_rf_model.predict_proba(latest)[0][1]  # Probability of the stock going up
    if (probability > 0.5):
        prediction = (f"📈 Based on historical trends and technical indicators, \n "
        f"the stock {stock_name} has a {round(probability * 100)}% probability of increasing in value over the next month.")
    else:
        prediction = (
        f"📉 Based on the current analysis, \n "
        f"the stock {stock_name} has a {round((1-probability) * 100)}% chance of declining in the upcoming month.")

    return prediction

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    stock_name = data.get('stock_name', None)

    if not stock_name:
        return jsonify({'error': 'Stock name is required'}), 400
    
    prediction = get_prediction(stock_name)

    return prediction
    


if __name__ == "__main__":
    app.run(debug = True)