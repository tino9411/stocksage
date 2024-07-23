import numpy as np
import pandas as pd

def calculate_ema(prices, period):
    return pd.Series(prices).ewm(span=period, adjust=False).mean().iloc[-1]

def calculate_macd(prices, fast=12, slow=26, signal=9):
    ema_fast = pd.Series(prices).ewm(span=fast, adjust=False).mean()
    ema_slow = pd.Series(prices).ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]

def calculate_bollinger_bands(prices, period=20, num_std_dev=2):
    rolling_mean = pd.Series(prices).rolling(window=period).mean()
    rolling_std = pd.Series(prices).rolling(window=period).std()
    upper_band = rolling_mean + (rolling_std * num_std_dev)
    lower_band = rolling_mean - (rolling_std * num_std_dev)
    return upper_band.iloc[-1], rolling_mean.iloc[-1], lower_band.iloc[-1]

def calculate_stochastic_oscillator(prices, low_prices, high_prices, period=14):
    low_min = pd.Series(low_prices).rolling(window=period).min()
    high_max = pd.Series(high_prices).rolling(window=period).max()
    k = 100 * (prices[-1] - low_min.iloc[-1]) / (high_max.iloc[-1] - low_min.iloc[-1])
    d = pd.Series(k).rolling(window=3).mean().iloc[-1]
    return k, d

def calculate_atr(high_prices, low_prices, close_prices, period=14):
    high = pd.Series(high_prices)
    low = pd.Series(low_prices)
    close = pd.Series(close_prices)
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    return atr.iloc[-1]

def calculate_obv(prices, volumes):
    obv = [volumes[0]]
    for i in range(1, len(prices)):
        if prices[i] > prices[i-1]:
            obv.append(obv[-1] + volumes[i])
        elif prices[i] < prices[i-1]:
            obv.append(obv[-1] - volumes[i])
        else:
            obv.append(obv[-1])
    return obv[-1]

def calculate_peg_ratio(pe_ratio, earnings_growth_rate):
    if pe_ratio is None or earnings_growth_rate is None or earnings_growth_rate == 0:
        return None
    try:
        return pe_ratio / earnings_growth_rate
    except ZeroDivisionError:
        return None
    except TypeError:
        return None
def calculate_debt_to_ebitda(total_debt, ebitda):
    if ebitda == 0:
        return None
    return total_debt / ebitda

def calculate_roic(net_income, dividends, total_debt, total_equity):
    invested_capital = total_debt + total_equity - dividends
    if invested_capital == 0:
        return None
    return (net_income - dividends) / invested_capital

def calculate_dividend_growth_rate(dividends, years):
    if len(dividends) < 2 or years < 1:
        return None
    start_dividend = dividends[0]
    end_dividend = dividends[-1]
    if start_dividend == 0:
        return None
    return (end_dividend / start_dividend) ** (1 / years) - 1