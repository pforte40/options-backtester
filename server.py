#!/usr/bin/env python3
"""
Options Backtester - Local API Server
Run this once: python server.py
Then open http://localhost:5050 in your browser.
"""

import json
import math
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
import threading
import webbrowser
import sys
import os

try:
    import yfinance as yf
    import pandas as pd
except ImportError:
    print("Missing dependencies. Installing...")
    os.system(f"{sys.executable} -m pip install yfinance pandas")
    import yfinance as yf
    import pandas as pd


HTML_FILE = os.path.join(os.path.dirname(__file__), "index.html")


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # suppress request logs

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "/index.html":
            self.serve_file()
        elif parsed.path == "/api/backtest":
            self.handle_backtest(parsed)
        else:
            self.send_error(404)

    def serve_file(self):
        try:
            with open(HTML_FILE, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404, "index.html not found")

    def handle_backtest(self, parsed):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            params = parse_qs(parsed.query)
            ticker      = params.get("ticker",      [""])[0].upper().strip()
            option_type = params.get("type",        ["CALL"])[0].upper().strip()
            strike      = float(params.get("strike",  [0])[0])
            expiry_str  = params.get("expiry",      [""])[0].strip()

            if not ticker:
                raise ValueError("Ticker is required.")
            if option_type not in ("CALL", "PUT"):
                raise ValueError("Option type must be CALL or PUT.")
            if strike <= 0:
                raise ValueError("Strike must be a positive number.")
            if not expiry_str:
                raise ValueError("Expiration date is required.")

            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
            today       = date.today()
            dte         = (expiry_date - today).days
            if dte < 1:
                raise ValueError("Expiration date must be in the future.")

            start = today - timedelta(days=230)
            df = yf.download(ticker, start=start, end=today, progress=False, auto_adjust=True)
            if df.empty:
                raise ValueError(f"No data found for '{ticker}'. Check the ticker symbol.")

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Ensure Open/Close exist regardless of column casing
            df.columns = [c.capitalize() for c in df.columns]
            df = df[["Open", "Close"]].dropna()

            # Capture dates from index (works with all yfinance versions)
            dates  = [pd.Timestamp(d).date() for d in df.index]
            opens  = df["Open"].tolist()
            closes = df["Close"].tolist()

            # For each start date, find the first trading day whose
            # calendar date >= start_date + dte calendar days
            def find_end_idx(start_i):
                target = dates[start_i] + timedelta(days=dte)
                for j in range(start_i + 1, len(dates)):
                    if dates[j] >= target:
                        return j
                return None  # ran out of data

            if len(opens) < 5:
                raise ValueError("Not enough trading day data returned for this ticker.")

            current_price = float(closes[-1])

            if option_type == "CALL":
                buffer_pct = ((strike - current_price) / current_price) * 100
            else:
                buffer_pct = ((current_price - strike) / current_price) * 100

            periods = []
            for i in range(len(opens)):
                end_i = find_end_idx(i)
                if end_i is None:
                    break  # ran out of data
                op = float(opens[i])
                cl = float(closes[end_i])
                if option_type == "CALL":
                    move = ((cl - op) / op) * 100
                else:
                    move = ((op - cl) / op) * 100
                periods.append({
                    "idx":        i + 1,
                    "start_date": str(dates[i]),
                    "end_date":   str(dates[end_i]),
                    "open":       round(op, 2),
                    "close":      round(cl, 2),
                    "move":       round(move, 4),
                    "breached":   bool(move >= buffer_pct),
                })

            last_180  = periods[-180:] if len(periods) > 180 else periods
            breaches  = sum(1 for p in last_180 if p["breached"])
            total     = len(last_180)
            breach_rate = round(breaches / total * 100, 1) if total else 0

            result = {
                "ok":            True,
                "ticker":        ticker,
                "option_type":   option_type,
                "current_price": round(current_price, 2),
                "strike":        round(strike, 2),
                "buffer_pct":    round(buffer_pct, 4),
                "dte":           dte,
                "expiry":        expiry_str,
                "total":         total,
                "breaches":      breaches,
                "breach_rate":   breach_rate,
                "periods":       last_180,
            }

        except Exception as ex:
            result = {"ok": False, "error": str(ex)}

        self.wfile.write(json.dumps(result).encode())


def main():
    port = 5050
    server = HTTPServer(("localhost", port), Handler)
    url = f"http://localhost:{port}"
    print(f"\n  Options Backtester running at {url}")
    print("  Press Ctrl+C to stop.\n")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")


if __name__ == "__main__":
    main()
