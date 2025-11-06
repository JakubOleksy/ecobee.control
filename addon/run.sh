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
bashio::log.info "Current /etc/resolv.conf:"
cat /etc/resolv.conf

# Test with getent which uses system resolver
if getent hosts auth.ecobee.com > /dev/null 2>&1; then
    bashio::log.info "DNS resolution working (getent test passed)"
elif nslookup auth.ecobee.com 172.30.32.3 > /dev/null 2>&1; then
    bashio::log.info "DNS resolution working (nslookup with explicit DNS passed)"
else
    bashio::log.error "DNS resolution failed - automation may not work"
fi

# Start the API server
cd /app
exec python3 api_server.py
