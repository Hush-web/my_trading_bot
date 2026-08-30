from freqtrade.strategy import IStrategy, IntParameter, DecimalParameter
from pandas import DataFrame
import talib.abstract as ta
import freqtrade.vendor.qtpylib.indicators as qtpylib
from datetime import datetime
from freqtrade.persistence import Trade

class SmartRegimeStrategy(IStrategy):
    # --- Timeframe (5-minutes for fast adaptability) ---
    timeframe = '5m'
    startup_candle_count: int = 200

    # --- Risk Management ---
    max_open_trades = 3
    stake_amount = 50

    # --- Regime Detection Threshold (ADX) ---
    adx_threshold = IntParameter(20, 30, default=25, space='buy')

    # --- Parameters for TRENDING Market (ADX > 25) ---
    buy_trend_rsi = IntParameter(45, 60, default=50, space='buy')
    sell_trend_rsi = IntParameter(45, 60, default=50, space='sell')

    # --- Parameters for RANGING Market (ADX < 25) ---
    buy_range_rsi = IntParameter(25, 40, default=30, space='buy')
    sell_range_rsi = IntParameter(60, 75, default=70, space='sell')

    # --- ROI (Dynamic: aggressive in range, relaxed in trend) ---
    minimal_roi = {
        "0": 0.04,
        "30": 0.02,
        "60": 0.01,
        "120": 0.0
    }

    # --- Stoploss (will be overridden by custom_stoploss) ---
    stoploss = -0.05

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)

        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=9)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=21)
        dataframe['ema_200'] = ta.EMA(dataframe, timeperiod=200)

        bollinger = qtpylib.bollinger_bands(qtpylib.typical_price(dataframe), window=20, stds=2)
        dataframe['bb_lower'] = bollinger['lower']
        dataframe['bb_middle'] = bollinger['mid']
        dataframe['bb_upper'] = bollinger['upper']

        dataframe['volume_mean'] = dataframe['volume'].rolling(20).mean()
        dataframe['volume_spike'] = dataframe['volume'] / dataframe['volume_mean']
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)

        return dataframe

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition_trend = (
            (dataframe['adx'] > self.adx_threshold.value) &
            (dataframe['ema_fast'] > dataframe['ema_slow']) &
            (dataframe['rsi'] > self.buy_trend_rsi.value) &
            (dataframe['close'] > dataframe['bb_upper'])
        )

        condition_range = (
            (dataframe['adx'] < self.adx_threshold.value) &
            (dataframe['rsi'] < self.buy_range_rsi.value) &
            (dataframe['close'] <= dataframe['bb_lower']) &
            (dataframe['volume_spike'] > 1.2)
        )

        dataframe.loc[condition_trend | condition_range, 'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        condition_trend_exit = (
            (dataframe['adx'] > self.adx_threshold.value) &
            (dataframe['rsi'] < self.sell_trend_rsi.value)
        )

        condition_range_exit = (
            (dataframe['adx'] < self.adx_threshold.value) &
            (dataframe['rsi'] > self.sell_range_rsi.value)
        )

        dataframe.loc[condition_trend_exit | condition_range_exit, 'sell'] = 1
        return dataframe

    def custom_stoploss(self, pair: str, trade: 'Trade', current_time: datetime,
                        current_rate: float, current_profit: float, **kwargs) -> float:
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        last_candle = dataframe.iloc[-1].squeeze()
        adx = last_candle['adx']

        if adx > self.adx_threshold.value:
            return -0.08
        else:
            return -0.025
