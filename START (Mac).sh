#!/bin/bash
echo "Installing dependencies (first run only)..."
pip3 install yfinance pandas --quiet
echo "Starting Options Backtester..."
python3 server.py
