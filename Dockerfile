FROM freqtradeorg/freqtrade:stable

# Copy your entire user_data folder into the container
COPY user_data /freqtrade/user_data

# Set the command to run your bot
CMD ["trade", "--config", "user_data/configs/config.json", "--strategy", "SecureFreqStrategy"]
