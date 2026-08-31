from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta

class MyStrategy(IStrategy):
    timeframe = '5m'
    startup_candle_count: int = 200

    max_open_trades = 3
    stake_amount = 50

    # Tight stoploss (cut losses fast)
    stoploss = -0.025

    # Trailing stop to lock in bounces
    trailing_stop = True
    trailing_stop_positive = 0.008
    trailing_stop_positive_offset = 0.015
    trailing_only_offset_is_reached = True

    # Take quick profits (scalp)
    minimal_roi = {
        "0": 0.02,   # 2% -> take it
        "15": 0.01,  # 1% after 15 min
        "30": 0.005, # 0.5% after 30 min
        "60": 0.0    # exit at breakeven if holding > 1 hour
    }

    # Hyperopt-ready params (tunable)
    buy_rsi = IntParameter(20, 35, default=28, space='buy')
    sell_rsi = IntParameter(55, 75, default=65, space='sell')
    bb_std = DecimalParameter(1.5, 2.5, default=2.0, space='buy')

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Bollinger Bands (dip detection)
        bollinger = ta.BBANDS(
            dataframe['close'],
            timeperiod=20,
            nbdevup=self.bb_std.value,
            nbdevdn=self.bb_std.value,
            matype=0
        )
        dataframe['bb_upper'] = bollinger['upperband']
        dataframe['bb_middle'] = bollinger['middleband']
        dataframe['bb_lower'] = bollinger['lowerband']

        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)

        # Volume spike (confirms panic selling)
        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        dataframe['volume_spike'] = dataframe['volume'] / dataframe['volume_mean']

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # 1. Oversold (panic)
                (dataframe['rsi'] < self.buy_rsi.value) &
                # 2. Price is at or below the lower Bollinger Band
                (dataframe['close'] <= dataframe['bb_lower']) &
                # 3. Volume confirms selling pressure (capitulation)
                (dataframe['volume_spike'] > 1.2) &
                # 4. Avoid extreme volatility (don't catch falling knives)
                (dataframe['atr'] / dataframe['close'] < 0.03)
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (
                # 1. Bounce is over (overbought)
                (dataframe['rsi'] > self.sell_rsi.value) |
                # 2. Price returns to the middle band (bounce fading)
                (dataframe['close'] >= dataframe['bb_middle'])
            ),
            'sell'] = 1
        return dataframe