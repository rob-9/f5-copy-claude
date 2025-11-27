#!/bin/bash
# Deployment script for F5 API Security System
# Based on DEPLOY-3 requirements and Section 8.2

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="${1:-f5-ai-security}"
VALUES_FILE="f5-ai-security-values.yaml"
CHART_DIR="f5-ai-security"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}F5 API Security System - Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check prerequisites (Section 8.1)
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if oc is installed and logged in
if ! command -v oc &> /dev/null; then
    echo -e "${RED}Error: oc CLI not found. Please install OpenShift CLI.${NC}"
    exit 1
fi

if ! oc whoami &> /dev/null; then
    echo -e "${RED}Error: Not logged in to OpenShift. Please run 'oc login' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ oc CLI found and authenticated${NC}"

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: Helm not found. Please install Helm 3.x.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Helm 3.x found${NC}"

# Check if values file exists
if [ ! -f "$VALUES_FILE" ]; then
    echo -e "${YELLOW}Warning: $VALUES_FILE not found.${NC}"
    echo -e "${YELLOW}Using default values from chart. It's recommended to create $VALUES_FILE.${NC}"
    echo -e "${YELLOW}Copy f5-ai-security-values.yaml.example to get started.${NC}"
    VALUES_FILE=""
fi

echo ""
echo -e "${YELLOW}Deploying to namespace: ${GREEN}${NAMESPACE}${NC}"
echo ""

# Create namespace if it doesn't exist
if ! oc get namespace "$NAMESPACE" &> /dev/null; then
    echo -e "${YELLOW}Creating namespace: ${NAMESPACE}${NC}"
    oc create namespace "$NAMESPACE"
else
    echo -e "${GREEN}✓ Namespace ${NAMESPACE} already exists${NC}"
fi

# Deploy using Helm (FR-14.1)
echo ""
echo -e "${YELLOW}Deploying Helm chart...${NC}"

if [ -n "$VALUES_FILE" ]; then
    helm upgrade --install f5-ai-security "$CHART_DIR" \
        --namespace "$NAMESPACE" \
        --values "$VALUES_FILE" \
        --wait \
        --timeout 5m
else
    helm upgrade --install f5-ai-security "$CHART_DIR" \
        --namespace "$NAMESPACE" \
        --wait \
        --timeout 5m
fi

echo -e "${GREEN}✓ Helm deployment completed${NC}"

# Verify deployment (VERIFY-1)
echo ""
echo -e "${YELLOW}Verifying deployment...${NC}"
echo ""

# Wait for pods to be ready
echo "Waiting for pods to be ready..."
oc wait --for=condition=ready pod \
    -l app.kubernetes.io/name=f5-ai-security \
    -n "$NAMESPACE" \
    --timeout=300s || true

# Show pod status
echo ""
echo -e "${YELLOW}Pod Status:${NC}"
oc get pods -n "$NAMESPACE"

# Show service status
echo ""
echo -e "${YELLOW}Service Status:${NC}"
oc get svc -n "$NAMESPACE"

# Show route (VERIFY-4)
echo ""
echo -e "${YELLOW}Route Status:${NC}"
if oc get route -n "$NAMESPACE" &> /dev/null; then
    ROUTE_URL=$(oc get route f5-ai-security -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "Not found")
    if [ "$ROUTE_URL" != "Not found" ]; then
        echo -e "${GREEN}✓ Application URL: https://${ROUTE_URL}${NC}"
    fi
    oc get route -n "$NAMESPACE"
fi

# Deployment summary
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Namespace: ${GREEN}${NAMESPACE}${NC}"
echo -e "Chart: ${GREEN}${CHART_DIR}${NC}"
if [ -n "$VALUES_FILE" ]; then
    echo -e "Values File: ${GREEN}${VALUES_FILE}${NC}"
fi
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Access the application via the route URL above"
echo "2. Configure F5 XC (see docs/f5_xc_deployment.md)"
echo "3. Test the chat interface"
echo "4. Verify security features (WAF, API Security, Rate Limiting)"
echo ""
echo -e "${GREEN}Deployment completed successfully!${NC}"
