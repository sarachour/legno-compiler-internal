#!/bin/bash

ARD_PATH="/Users/sachour/Documents/Arduino/libraries/HCDC_DEMO_API"
NOW=$(date "+%Y.%m.%d-%H.%M.%S")
echo cp -v "${PWD}/HCDC_DEMO_API/*" "${ARD_PATH}/"
cp -v ${PWD}/HCDC_DEMO_API/* ${ARD_PATH}/

