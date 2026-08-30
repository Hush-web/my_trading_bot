from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta

class MeanReversionScalper(IStrategy):
    timeframe = '5m'
    startup_candle_count: int = 200

    max_open_trades = 3
    stake_amount = 50

    stoploss = -0.025

    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.015
    trailing_only_offset_is_reached = True

    minimal_roi = {
        "0": 0.02,
        "15": 0.01,
        "30": 0.005,
        "60": 0.0
    }

    buy_rsi = IntParameter(20, 35, default=28, space='buy')
    sell_rsi = IntParameter(55, 75, default=65, space='sell')
    bb_std = DecimalParameter(1.5, 2.5, default=2.0, space='buy')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Bollinger Bands using TA-Lib (no qtpylib)
        bollinger = ta.BBANDS(
            dataframe['close'],
            timeperiod=20,
            nbdevup=self.bb_std.value,
            nbdevdn=self.bb_std.value,
            matype=0  # Simple Moving Average
        )
        dataframe['bb_upper'] = bollinger['upperband']
        dataframe['bb_middle'] = bollinger['middleband']
        dataframe['bb_lower'] = bollinger['lowerband']

        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)

        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        dataframe['volume_spike'] = dataframe['volume'] / dataframe['volume_mean']

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] < self.buy_rsi.value) &
                (dataframe['close'] <= dataframe['bb_lower']) &
                (dataframe['volume_spike'] > 1.2) &
                (dataframe['atr'] / dataframe['close'] < 0.03)
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] > self.sell_rsi.value) |
                (dataframe['close'] >= dataframe['bb_middle'])
            ),
            'sell'] = 1
        return dataframe