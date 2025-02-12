#!/bin/bash -e

#-----------------------------------------------------------------------------------------
# Script information
script_name='DRYES SSMI'
script_version="1.1.2"
script_date='2023/10/17'

virtualenv_folder=''
virtualenv_name=''
script_folder=''

# Execution example:
# python3 dryes_SSMI_main.py -settings_file "configuration.json" -time_now "yyyy-mm-dd HH:MM" -time_history_start "yyyy-mm-dd HH:MM" -time_history_end  "yyyy-mm-dd HH:MM"
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Get file information
script_file='/home/dryes_SSMI_main.py'
settings_file='/home/dryes_SSMI.json'

# Get information (-u to get gmt time)
#time_now=$(date -u +"%Y-%m-%d %H:00")
time_now='2023-06-01 00:00' # DEBUG 
time_history_start='1992-01-01 00:00' # DEBUG 
time_history_end='2021-12-31 00:00' # DEBUG 
#-----------------------------------------------------------------------------------------

#-----------------------------------------------------------------------------------------
# Activate virtualenv
export PATH=$virtualenv_folder/bin:$PATH
source activate $virtualenv_name

# Add path to pythonpath
export PYTHONPATH="${PYTHONPATH}:$script_folder"
#-----------------------------------------------------------------------------------------

# ----------------------------------------------------------------------------------------
# Info script start
echo " ==================================================================================="
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> START ..."
echo " ==> COMMAND LINE: " python3 $script_file -settings_file $settings_file -time $time_now

# Run python script (using setting and time)
python3 $script_file -settings_file $settings_file -time_now "$time_now" -time_history_start "$time_history_start" -time_history_end "$time_history_end"

# Info script end
echo " ==> "$script_name" (Version: "$script_version" Release_Date: "$script_date")"
echo " ==> ... END"
echo " ==> Bye, Bye"
echo " ==================================================================================="
# ----------------------------------------------------------------------------------------

