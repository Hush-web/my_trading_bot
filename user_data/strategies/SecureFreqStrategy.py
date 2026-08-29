from freqtrade.strategy import IStrategy, IntParameter
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib

class SecureFreqStrategy(IStrategy):
    timeframe = '5m'
    startup_candle_count = 200

    max_open_trades = 3
    stake_amount = 50
    stoploss = -0.03

    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.015
    trailing_only_offset_is_reached = True

    minimal_roi = {
        "0": 0.05,
        "30": 0.03,
        "60": 0.01,
        "120": 0.0
    }

    buy_ema_short = IntParameter(5, 15, default=9, space='buy')
    buy_ema_long = IntParameter(15, 30, default=21, space='buy')
    buy_rsi = IntParameter(45, 60, default=50, space='buy')
    sell_rsi = IntParameter(45, 60, default=50, space='sell')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['ema_short'] = ta.EMA(dataframe, timeperiod=self.buy_ema_short.value)
        dataframe['ema_long'] = ta.EMA(dataframe, timeperiod=self.buy_ema_long.value)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['atr_percent'] = (dataframe['atr'] / dataframe['close']) * 100
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_mean']
        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['ema_short'] > dataframe['ema_long']) &
                (dataframe['rsi'] > self.buy_rsi.value) &
                (dataframe['atr_percent'] < 3.0) &
                (dataframe['volume_ratio'] > 0.8)
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['ema_short'] < dataframe['ema_long']) |
                (dataframe['rsi'] < self.sell_rsi.value)
            ),
            'sell'] = 1
        return dataframe
