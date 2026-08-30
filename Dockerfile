FROM freqtradeorg/freqtrade:stable
COPY user_data /freqtrade/user_data
CMD ["--config", "user_data/configs/config.json", "--strategy", "MyStrategy"]