#!/bin/sh

# Get the path to the config file
CONFIG_FILE=/usr/share/nginx/html/config.js

# Replace the placeholder with the runtime environment variable
# Using a different delimiter for sed to handle URLs safely
sed -i "s|__VITE_API_BASE_URL__|${VITE_API_BASE_URL}|g" $CONFIG_FILE

# Start NGINX in the foreground
echo "Starting NGINX..."
nginx -g 'daemon off;'
