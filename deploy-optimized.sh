#!/bin/bash

# Alpha Design Spot - Optimized Deployment Script
set -e

echo "🚀 Starting Alpha Design Spot optimized deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_DIR="/home/Alpha-Design-Spot"
SERVICE_NAME="ads"
SOCKET_NAME="ads.socket"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root"
   exit 1
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p /var/log/ads
mkdir -p /run/ads
chown -R root:www-data /var/log/ads
chown -R www-data:www-data /run/ads

# Stop existing services
print_status "Stopping existing services..."
systemctl stop $SERVICE_NAME 2>/dev/null || true
systemctl stop $SOCKET_NAME 2>/dev/null || true

# Copy service files
print_status "Installing optimized service files..."
cp $PROJECT_DIR/ads-optimized.service /etc/systemd/system/$SERVICE_NAME.service
cp $PROJECT_DIR/ads.socket /etc/systemd/system/$SOCKET_NAME

# Reload systemd
print_status "Reloading systemd daemon..."
systemctl daemon-reload

# Enable services
print_status "Enabling services..."
systemctl enable $SOCKET_NAME
systemctl enable $SERVICE_NAME

# Start socket (this will start the service automatically when needed)
print_status "Starting socket..."
systemctl start $SOCKET_NAME

# Wait a moment and check status
sleep 3
print_status "Checking service status..."

if systemctl is-active --quiet $SOCKET_NAME; then
    print_status "✅ Socket is active"
else
    print_error "❌ Socket failed to start"
    systemctl status $SOCKET_NAME
    exit 1
fi

# Test the application
print_status "Testing application..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/auth/health | grep -q "200"; then
    print_status "✅ Application is responding"
else
    print_warning "⚠️  Application health check failed - checking logs..."
    journalctl -u $SERVICE_NAME --no-pager -n 20
fi

# Update Nginx configuration (optional)
if [[ -f "/etc/nginx/sites-available/ads" ]]; then
    print_status "Backing up existing Nginx config..."
    cp /etc/nginx/sites-available/ads /etc/nginx/sites-available/ads.backup.$(date +%Y%m%d_%H%M%S)
    
    print_status "Installing optimized Nginx config..."
    cp $PROJECT_DIR/nginx-ads-optimized.conf /etc/nginx/sites-available/ads
    
    # Test nginx config
    if nginx -t; then
        print_status "✅ Nginx config is valid"
        print_status "Reloading Nginx..."
        systemctl reload nginx
    else
        print_error "❌ Nginx config is invalid - reverting..."
        cp /etc/nginx/sites-available/ads.backup.$(date +%Y%m%d_%H%M%S) /etc/nginx/sites-available/ads
    fi
fi

print_status "🎉 Deployment completed!"
print_status ""
print_status "📊 Service Status:"
systemctl status $SERVICE_NAME --no-pager -l
print_status ""
print_status "📋 Useful commands:"
echo "  - Check logs: journalctl -u $SERVICE_NAME -f"
echo "  - Restart service: systemctl restart $SERVICE_NAME"
echo "  - Check socket: systemctl status $SOCKET_NAME"
echo "  - Test health: curl http://localhost/api/auth/health"
print_status ""
print_status "🔧 Configuration optimizations applied:"
echo "  ✅ Reduced workers from 9 to 6 (more efficient)"
echo "  ✅ Reduced timeout from 120s to 60s (faster failure detection)"
echo "  ✅ Added worker recycling (prevents memory leaks)"
echo "  ✅ Added Unix socket communication (faster than TCP)"
echo "  ✅ Added resource limits and security hardening"
echo "  ✅ Improved logging and monitoring"
echo "  ✅ Added graceful restart handling"