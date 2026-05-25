# Options Backtester

A local web app for backtesting option trades using 180 days of historical data.

## Requirements

- Python 3.8 or later  (https://python.org/downloads)
- Internet connection (to fetch Yahoo Finance data)

## How to start

### Windows
Double-click:  START (Windows).bat

### Mac / Linux
1. Open Terminal in this folder
2. Run:  chmod +x "START (Mac).sh" && ./"START (Mac).sh"

The app will automatically open in your browser at http://localhost:5050

## How it works

1. Enter a ticker (e.g. AAPL), select CALL or PUT, enter your strike price and expiration date
2. Click Run Backtest
3. The app calculates:
   - Buffer: % move required from current price to reach your strike
   - DTE: calendar days to expiration
   - Rolling periods: using DTE as the window length, rolled 1 day at a time across 180 days
   - Each period compares Open on day 0 to Close on day +DTE
   - Breach: CALL = stock moved UP ≥ buffer%; PUT = stock moved DOWN ≥ buffer%
4. Results show a summary, chart, and full period table
5. Export to CSV with one click

## To stop the server
Press Ctrl+C in the terminal / command prompt window.
