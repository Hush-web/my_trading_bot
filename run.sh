#!/bin/sh
trade --config user_data/configs/config.json --strategy SecureFreqStrategy 2>&1
echo "Bot exited with code $?"
sleep 3600