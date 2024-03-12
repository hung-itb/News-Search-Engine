#!/bin/sh

>> config.js
# Find all the FRONTEND_API_ environment variables in the environment
customVars=""
for key in $(env | awk -F "=" '{print $1}' | grep ".*FRONTEND_API_.*")
do
  customVars="$customVars$key "
done

# Recreate a new config.js
for key in $customVars
do
  eval "value=\$$key"
  echo "window.$key='$value';" >> config.js
done