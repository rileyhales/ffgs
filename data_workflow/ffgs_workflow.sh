#!/usr/bin/env bash
# activate the python environment containing the dependencies to run the workflow
source /media/root/tethys/main/tethys/miniconda/etc/profile.d/conda.sh; conda activate tethys
# exectue the workflow using the path to the gfsworkflow.py file and the path to save the data
python /home/civil/apps/ffgs/data_workflow/gfsworkflow.py /home/civil/thredds_data/ffgs/
python /home/civil/apps/ffgs/data_workflow/wrfprworkflow.py /home/civil/thredds_data/ffgs/

# then run this command from crontab with a command like:
# 0 4 * * * bash /path/to/workflow/ffgs_workflow.sh