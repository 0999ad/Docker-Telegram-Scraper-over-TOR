#!/bin/bash
# Start Tor service
service tor start

# Check Tor status
# Add your own checks or logs here to confirm Tor is running

# Simple sleep to wait for Tor to initialize (optional, depending on your setup)
sleep 10


# Execute the CMD from the Dockerfile, e.g., start Flask
exec "$@"
