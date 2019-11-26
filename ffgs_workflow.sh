#!/usr/bin/env bash
# activate the python environment containing the dependencies to run the workflow
source /media/root/tethys/main/tethys/miniconda/etc/profile.d/conda.sh; conda activate tethys
# exectue the workflow using the path to the gfsworkflow.py file and the path to save the data
python /media/root/tethys/main/tethys/apps/ffgs/tethysapp/ffgs/gfsworkflow.py /media/root/tethys/main/thredds/data/thredds/public/ffgs/ /media/root/tethys/main/tethys/apps/ffgs/tethysapp/ffgs/workspaces/app_workspace
python /media/root/tethys/main/tethys/apps/ffgs/tethysapp/ffgs/wrfprworkflow.py /media/root/tethys/main/thredds/data/thredds/public/ffgs/ /media/root/tethys/main/tethys/apps/ffgs/tethysapp/ffgs/workspaces/app_workspace

# then run this command from crontab with a command like:
# 0 4 * * * bash /path/to/workflow/ffgs_workflow.sh