# Trading simulator 

# Database for positions and trades

# Display PNL through LCD on Pi and website

# Seperate URL for importing trades 

# API for fetching coin prices 

# (Additional - add a live price of BTC with AJAX) 

# Bootstrap for UI

# ------------------------------------------ #

# Importing Libraries

from flask import Flask, request, flash, json, redirect 
from flask import render_template
import sqlite3
import asyncio
import websockets
import pandas as pd
import sqlalchemy as sqla
import ccxt

app = Flask(__name__)

global cursor
global connection
connection = sqlite3.connect('trades.db', check_same_thread=False)
cursor = connection.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT, coin TEXT, amount FLOAT, usd FLOAT, entryprice FLOAT, currentprice FLOAT, profitloss FLOAT)")
exchange_id = 'binance'
exchange_class = getattr(ccxt, exchange_id)
exchange = exchange_class({
    'apiKey': 'FboyssPKoBtfkOgCW7YQPzKxOCrRW3ZZTyUYC3JjfIgUV3S5cQxjSoqSA1uqXu8F',
    'secret': 'zEe3pMmuO3OqovIZOpYb20QWGiudJg5tJ1SIZ8fKPAnzMYj2r5r2R18VgBIQQYbk',
    'timeout': 30000,
    'enableRateLimit': True,
})

def fetch_coin_price(coins):
    if (exchange.has['fetchTicker']):
        coin_pair = '{0}/USDT'.format(coins)
        get_price = exchange.fetch_ticker(coin_pair)
        coin_price = get_price['info']['lastPrice']    
    return coin_price
@app.route('/', methods=["POST", "GET"])
def index():
    global total_pnl
    global total_portfolio
    update_pnl()
    
    info = panda_dataframe()
    
    command = 'SELECT profitloss from trades'
    data = cursor.execute(command).fetchall()
    pnl_balance = []
    for price in data:
        x = str(price)
        x = x.strip("(),")
        x = float(x)
        pnl_balance.append(x)
    
    command = 'SELECT usd from trades'
    data = cursor.execute(command).fetchall()
    portfolio = []
    for price in data:
        x = str(price)
        x = x.strip("(),")
        x = float(x)
        portfolio.append(x)
    
    total_pnl = sum(pnl_balance) 
    total_pnl = float(total_pnl)
    total_pnl = '{:.2f}'.format(total_pnl)
    
    total_portfolio = sum(portfolio)
    total_portfolio = float(total_portfolio)
    total_portfolio = '{:.2f}'.format(total_portfolio)






    return render_template("index.html", total_pnl=float(total_pnl), total_portfolio=total_portfolio,  tables=[info.to_html(classes='table table-responsive table-dark')], titles=info.columns.values)



# Updates Portfolio in home page
def total_pnl():
    global total_pnl
    command = 'SELECT profitloss from trades'
    data = cursor.execute(command).fetchall()
    pnl_balance = []
    for price in data:
        x = str(price)
        x = x.strip("(),")
        x = float(x)
        pnl_balance.append(x)
    
    total_pnl = sum(pnl_balance)
    total_pnl = float(total_pnl)
    total_pnl = total_pnl
    return total_pnl
    

def portfolio():
    global total_portfolio 
    command = 'SELECT usd from trades'
    data = cursor.execute(command).fetchall()
    portfolio = []
    for price in data:
        x = str(price)
        x = x.strip("(),")
        x = float(x)
        portfolio.append(x)
    
    total_portfolio = sum(portfolio)
    total_portfolio = float(total_portfolio)
    total_portfolio = total_portfolio
    return total_portfolio




# Update PNL table in home page and entry price in the home page.
def update_pnl():
    print('Updating PNL...') 
    list_of_coins = cursor.execute('SELECT coin from trades').fetchall()
    coins_appended = []
    for coins in list_of_coins:
        string = str(coins)
        stripped = string.strip("(),'")
        coins_appended.append(stripped)
    print('Open trades', coins_appended)
    for x in coins_appended:
        coin = fetch_coin_price(x)
        print(x, coin)
        command = "UPDATE trades SET currentprice = {0} WHERE coin = '{1}'".format(float(coin), x)
        cursor.execute(command)
        connection.commit()
        command = 'SELECT entryprice from trades WHERE coin = "{0}"'.format(x)
        coin_entry = cursor.execute(command).fetchone()
        coin_entry = str(coin_entry)
        coin_entry = coin_entry.strip("(),")
        
        command = "SELECT amount from trades where coin = '{0}'".format(x)
        amount_coins = cursor.execute(command).fetchone()
        amount_coins = str(amount_coins)
        amount_coins = amount_coins.strip("(),")

        profitloss = ((float(fetch_coin_price(x)) * float(amount_coins)) - (float(coin_entry) * float(amount_coins))) 
        command = "UPDATE trades SET profitloss = {0} WHERE coin = '{1}'".format(float(profitloss), x)
        cursor.execute(command)
        connection.commit()





def panda_dataframe():
    db = sqla.create_engine('sqlite:///trades.db')
    datas=pd.read_sql('SELECT * FROM trades', db)
    #datas['price'] = datas['price'].map('${:,.4f}'.format)
    #datas['amount'] = datas['amount'].map('{:,.8f}'.format)
    print(datas)
    return datas


# -- Page to import new trades to database -- #
@app.route('/trades', methods=["POST", "GET"])
def trades():

    if request.method == "POST":

        coin = request.form["coin"]
        position = request.form["position_size"]

        print("COIN, POSITION", coin, position)
        #return redirect(request.url)    
        #command = 'INSERT INTO trades(coin, amount) VALUES("{0}", {1})'.format(coin, position)
      
       # connection = sqlite3.connect('trades.db', check_same_thread=False)
     
       # cursor = connection.cursor()
       # cursor.execute("CREATE TABLE IF NOT EXISTS trades(id INTEGER PRIMARY KEY AUTOINCREMENT, coin TEXT, amount FLOAT, usd FLOAT, entryprice FLOAT, profitloss FLOAT)")
        coin_price = fetch_coin_price(coin)
        usd_amount = float(coin_price) * float(position)
        command = 'INSERT INTO trades(coin, amount, usd, entryprice) VALUES("{0}", {1}, {2}, {3})'.format(coin, float(position), float(usd_amount), float(coin_price))

        
        cursor.execute(command)
        connection.commit()
        # GET CURRENT PRICE OF COIN W/ PUBLIC API THEN APPEND TO DATABASE. 
        # Position_in_USD = amount x coinPrice
        
    return render_template("trades.html")
@app.route('/edit_trades', methods = ["POST", "GET"])
def edit_trades():
    if request.method == "POST":

        coin = request.form["coin"]
        print('DELETE COIN:',coin)
        command = 'DELETE FROM trades WHERE coin = "{0}"'.format(coin)
        
        cursor.execute(command)
        connection.commit()
    return render_template("edit_trades.html")

@app.route('/delete', methods = ["POST", "GET"])
def delete():
    if request.method == "POST":
        print('Deleting trades')
        command = 'DELETE FROM trades'
        
        cursor.execute(command)
        connection.commit()
    return redirect('/edit_trades')

@app.route('/info', methods = ["POST", "GET"])
def info():
    return render_template("info.html")
app.run(host="0.0.0.0", port = 5000, debug = True)
