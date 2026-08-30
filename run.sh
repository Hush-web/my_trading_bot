#!/bin/bash
trade --config user_data/configs/config.json --strategy SecureFreqStrategy --verbosity 3 > /tmp/bot.log 2>&1
echo "Exit code: $?" >> /tmp/bot.log
sleep 3600