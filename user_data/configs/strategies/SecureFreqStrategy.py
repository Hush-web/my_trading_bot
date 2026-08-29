# user_data/strategies/SecureFreqStrategy.py
from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class SecureFreqStrategy(IStrategy):
    # --- Core Settings ---
    timeframe = '5m'
    startup_candle_count: int = 200

    # --- Risk Management (Tight & Secure) ---
    max_open_trades = 3
    stake_amount = 50

    # Hard stoploss (last resort)
    stoploss = -0.03  # 3% max loss

    # Trailing stop (locks in profits)
    trailing_stop = True
    trailing_stop_positive = 0.01        # Lock 1% profit
    trailing_stop_positive_offset = 0.015 # Start trailing at 1.5% profit
    trailing_only_offset_is_reached = True

    # Time-based exits (take profits quickly)
    minimal_roi = {
        "0": 0.05,   # 5% profit -> exit immediately
        "30": 0.03,  # 3% profit after 30 minutes
        "60": 0.01,  # 1% profit after 1 hour
        "120": 0.0   # exit at breakeven after 2 hours
    }

    # --- Hyperopt-ready parameters (tune later) ---
    buy_ema_short = IntParameter(5, 15, default=9, space='buy')
    buy_ema_long = IntParameter(15, 30, default=21, space='buy')
    buy_rsi = IntParameter(45, 60, default=50, space='buy')
    sell_rsi = IntParameter(45, 60, default=50, space='sell')

    # --- Indicators ---
    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # EMAs for momentum
        dataframe['ema_short'] = ta.EMA(dataframe, timeperiod=self.buy_ema_short.value)
        dataframe['ema_long'] = ta.EMA(dataframe, timeperiod=self.buy_ema_long.value)

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # ATR – Volatility filter (security)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['atr_percent'] = (dataframe['atr'] / dataframe['close']) * 100

        # Volume filter
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_mean']

        return dataframe

    # --- Buy Signal ---
    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # 1. Fast EMA crosses above Slow EMA (momentum up)
                (dataframe['ema_short'] > dataframe['ema_long']) &
                # 2. RSI > 50 (bullish momentum)
                (dataframe['rsi'] > self.buy_rsi.value) &
                # 3. Avoid extreme volatility (ATR < 3% of price)
                (dataframe['atr_percent'] < 3.0) &
                # 4. Volume is not drying up
                (dataframe['volume_ratio'] > 0.8)
            ),
            'buy'] = 1
        return dataframe

    # --- Sell Signal ---
    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # 1. Momentum reverses (Fast EMA drops below Slow EMA)
                (dataframe['ema_short'] < dataframe['ema_long']) |
                # 2. RSI drops below 50 (momentum lost)
                (dataframe['rsi'] < self.sell_rsi.value)
            ),
            'sell'] = 1
        return dataframe