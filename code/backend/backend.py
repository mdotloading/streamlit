from flask import Flask, request, jsonify # Flask für REST-API, Request-Handling und JSON-Ausgabe
import yfinance as yf 
import os

app = Flask(__name__)

@app.route("/api/stock", methods=["GET"]) # Endpoint: /api/stock
def get_stock_data():
    ticker = request.args.get("ticker", "AAPL") # Query-Param Ticker, Default AAPL
    print(f"Fetching: {ticker}")
    start = request.args.get("start", "2023-07-03") # Startdatum mit Default
    end = request.args.get("end", "2025-07-04")     # Enddatum mit Default
    data = yf.download(ticker, start=start, end=end, progress=False).dropna() # Börsendaten laden

    if data.empty: # Falls keine Daten zurückkommen → 404
        return jsonify([]), 404

    data.columns = data.columns.get_level_values(0)  # Spaltennamen flach machen (MultiIndex entfernen)
    data = data.reset_index() # Datum wieder als normale Spalte
    return jsonify(data.to_dict(orient="records")) # in JSON konvertieren und zurückgeben

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000)) # PORT aus Env oder Default 5000
    app.run(host="0.0.0.0", port=port, debug=True) # Startet Flask-Server, erreichbar von außen
