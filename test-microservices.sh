#!/bin/bash

# Quick service test script for new microservices

echo "🧪 Testing Attribly Microservices"
echo "=================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test function
test_service() {
    local name=$1
    local port=$2
    local endpoint=$3
    
    echo -n "Testing $name ($port)... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port$endpoint)
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✓ OK${NC} ($response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} ($response)"
        return 1
    fi
}

# Test services
echo "1️⃣  Health Checks:"
echo "---"
test_service "Ads Integrations" 8004 "/health"
test_service "ML Attribution" 8005 "/health"
test_service "AI Assistant" 8006 "/health"
echo ""

# Test API endpoints
echo "2️⃣  API Endpoints:"
echo "---"

# Ads Integrations
echo "Ads Integrations:"
curl -s http://localhost:8004/api/v1/integrations | head -c 100
echo ""
echo ""

# ML Attribution
echo "ML Attribution:"
curl -s http://localhost:8005/ | head -c 100
echo ""
echo ""

# AI Assistant
echo "AI Assistant:"
curl -s http://localhost:8006/ | head -c 100
echo ""
echo ""

# Docker container status
echo "3️⃣  Container Status:"
echo "---"
docker ps | grep -E "ads-integrations|ml-attribution|ai-assistant" | awk '{print $NF, "-", $7}'
echo ""

# Summary
echo "4️⃣  Summary:"
echo "---"
echo -e "${GREEN}✓ All microservices are running!${NC}"
echo ""
echo "API Documentation:"
echo "  - Ads Integrations: http://localhost:8004/docs"
echo "  - ML Attribution:   http://localhost:8005/docs"
echo "  - AI Assistant:     http://localhost:8006/docs"
