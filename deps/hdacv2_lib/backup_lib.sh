#!/bin/bash

ARD_PATH="/Users/sachour/Documents/Arduino/libraries/HCDC_DEMO_API"
NOW=$(date "+%Y.%m.%d-%H.%M.%S")
echo tar -cvzf hcdc_api_${NOW}.tgz ${ARD_PATH}
tar -cvzf hcdc_api_${NOW}.tgz ${ARD_PATH}

