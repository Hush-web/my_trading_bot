FROM freqtradeorg/freqtrade:stable
COPY user_data /freqtrade/user_data
CMD ["trade", "--config", "user_data/configs/config.json", "--strategy", "MyStrategy"]