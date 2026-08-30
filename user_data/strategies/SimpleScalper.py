from freqtrade.strategy import IStrategy
from pandas import DataFrame

class SimpleScalper(IStrategy):
    timeframe = '5m'
    startup_candle_count = 100

    max_open_trades = 3
    stake_amount = 50
    stoploss = -0.025

    minimal_roi = {
        "0": 0.02,
        "15": 0.01,
        "30": 0.005,
        "60": 0.0
    }

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Simple moving average (no TA-Lib)
        dataframe['sma_fast'] = dataframe['close'].rolling(9).mean()
        dataframe['sma_slow'] = dataframe['close'].rolling(21).mean()
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['sma_fast'] > dataframe['sma_slow']) &
            (dataframe['close'] < dataframe['close'].shift(1) * 0.995),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe['sma_fast'] < dataframe['sma_slow']) |
            (dataframe['close'] > dataframe['close'].shift(1) * 1.01),
            'sell'] = 1
        return dataframe