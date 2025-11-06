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

# Test DNS resolution
bashio::log.info "Testing DNS resolution..."
if nslookup auth.ecobee.com > /dev/null 2>&1; then
    bashio::log.info "DNS resolution working"
else
    bashio::log.warning "DNS resolution failed - checking /etc/resolv.conf"
    cat /etc/resolv.conf || bashio::log.error "Cannot read /etc/resolv.conf"
fi

# Start the API server
cd /app
exec python3 api_server.py
