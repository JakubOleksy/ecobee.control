#!/usr/bin/with-contenv bashio

# Get configuration from add-on options
export ECOBEE_USERNAME=$(bashio::config 'ecobee_username')
export ECOBEE_PASSWORD=$(bashio::config 'ecobee_password')
export WEBDRIVER_HEADLESS=$(bashio::config 'webdriver_headless')
export LOG_LEVEL=$(bashio::config 'log_level')
export API_PORT=$(bashio::config 'api_port')

# Create .secrets file from options
cat > /app/.secrets << EOF
ECOBEE_USERNAME=${ECOBEE_USERNAME}
ECOBEE_PASSWORD=${ECOBEE_PASSWORD}
EOF

# Log startup
bashio::log.info "Starting Ecobee Web Control API server..."
bashio::log.info "API will be available on port ${API_PORT}"

# Start the API server
cd /app
exec python3 api_server.py
