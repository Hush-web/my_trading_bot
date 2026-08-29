FROM freqtradeorg/freqtrade:stable

# Copy your strategy and config into the container
COPY user_data /freqtrade/user_data

# Start the bot with your strategy
CMD ["trade", "--config", "user_data/configs/config.json", "--strategy", "SecureFreqStrategy"]
