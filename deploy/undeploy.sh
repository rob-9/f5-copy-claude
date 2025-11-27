#!/bin/bash
# Cleanup script for F5 API Security System
# Removes all deployed resources

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
NAMESPACE="${1:-f5-ai-security}"
RELEASE_NAME="f5-ai-security"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}F5 API Security System - Cleanup${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

# Confirm deletion
echo -e "${RED}WARNING: This will delete all resources in namespace: ${NAMESPACE}${NC}"
echo -e "${RED}Release name: ${RELEASE_NAME}${NC}"
echo ""
read -p "Are you sure you want to continue? (yes/no): " -r
echo ""

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${GREEN}Cleanup cancelled.${NC}"
    exit 0
fi

# Check if oc is installed
if ! command -v oc &> /dev/null; then
    echo -e "${RED}Error: oc CLI not found.${NC}"
    exit 1
fi

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo -e "${RED}Error: Helm not found.${NC}"
    exit 1
fi

# Delete Helm release
echo -e "${YELLOW}Uninstalling Helm release...${NC}"
if helm list -n "$NAMESPACE" | grep -q "$RELEASE_NAME"; then
    helm uninstall "$RELEASE_NAME" -n "$NAMESPACE"
    echo -e "${GREEN}✓ Helm release uninstalled${NC}"
else
    echo -e "${YELLOW}Helm release not found, skipping...${NC}"
fi

# Optional: Delete namespace
echo ""
read -p "Do you want to delete the namespace '$NAMESPACE' as well? (yes/no): " -r
echo ""

if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    if oc get namespace "$NAMESPACE" &> /dev/null; then
        echo -e "${YELLOW}Deleting namespace: ${NAMESPACE}${NC}"
        oc delete namespace "$NAMESPACE"
        echo -e "${GREEN}✓ Namespace deleted${NC}"
    else
        echo -e "${YELLOW}Namespace not found, skipping...${NC}"
    fi
fi

echo ""
echo -e "${GREEN}Cleanup completed successfully!${NC}"
