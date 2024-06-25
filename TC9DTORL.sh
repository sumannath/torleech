#!/bin/bash
#--------------------------------------------------------------------------------------------#
#   Script to run the TorLeech login
#   Add in cron as follows:
#   0 0,6,12,18 * * * /home/suman/torleech/TC9DTORL.sh
#--------------------------------------------------------------------------------------------#
export WORKING_PATH="/home/suman/torleech"

# Activate python environment
source "${WORKING_PATH}/venv/bin/activate"

# Run the Python script
python "${WORKING_PATH}/main.py"
