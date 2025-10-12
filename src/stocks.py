#!/usr/bin/env python3
'''
This scripts compare the stock prices of ANET against the magnificent 7 except
Nvidia, starting from 2014-07-01 which was my starting date at Arista.
'''

# pylint: disable=import-error
import yfinance as yf
import matplotlib.pyplot as plt

def plot_ticker_growth(tickers, start="2020-01-01", end=None):
    """
    Download historical closing prices for given stock tickers and plot their normalized growth.

    Parameters:
        tickers (list[str]): list of ticker symbols (e.g., ["AAPL", "MSFT", "GOOGL"])
        start (str): start date in 'YYYY-MM-DD' format
        end (str): end date in 'YYYY-MM-DD' format (default: today)
    """
    # Download data
    data = yf.download(tickers, start=start, end=end)
    if data is None:
        print(f'Unable to fetch data')
        return
    data = data['Close']

    # Normalize so that all series start at 100 for easy comparison
    normalized = data / data.iloc[0] * 100

    # Plot
    plt.figure(figsize=(12, 6))
    for ticker in normalized.columns:
        plt.plot(normalized.index, normalized[ticker], label=ticker)

    plt.title("Stock Growth Comparison (Normalized to 100)")
    plt.xlabel("Date")
    plt.ylabel("Normalized Price (Base = 100)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Example usage
if __name__ == "__main__":
    tickers = ["AAPL", "AMZN", "ANET", "GOOGL", "META", "MSFT", "NFLX" ]
    STARTING_DATE = '2014-07-01'
    plot_ticker_growth(tickers, start=STARTING_DATE)
