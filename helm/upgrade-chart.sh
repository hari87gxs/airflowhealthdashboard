#!/bin/bash
# Helper script to upgrade an existing Helm release

set -e

CHART_DIR="./airflow-health-dashboard"
RELEASE_NAME="${1:-airflow-health}"
NAMESPACE="${2:-airflow-health}"
VALUES_FILE="${3:-}"

echo "🔄 Upgrading Airflow Health Dashboard"
echo "   Release: $RELEASE_NAME"
echo "   Namespace: $NAMESPACE"

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed. Please install Helm 3.x"
    exit 1
fi

# Check if release exists
if ! helm status "$RELEASE_NAME" -n "$NAMESPACE" &> /dev/null; then
    echo "❌ Release '$RELEASE_NAME' not found in namespace '$NAMESPACE'"
    echo "   Use install-chart.sh to install a new release"
    exit 1
fi

# Show current release info
echo ""
echo "📊 Current release info:"
helm status "$RELEASE_NAME" -n "$NAMESPACE" | head -n 10

# Build helm upgrade command
HELM_CMD="helm upgrade $RELEASE_NAME $CHART_DIR --namespace $NAMESPACE"

if [ -n "$VALUES_FILE" ]; then
    if [ ! -f "$VALUES_FILE" ]; then
        echo "❌ Values file not found: $VALUES_FILE"
        exit 1
    fi
    echo "📋 Using values file: $VALUES_FILE"
    HELM_CMD="$HELM_CMD -f $VALUES_FILE"
fi

# Add flags for safer upgrade
HELM_CMD="$HELM_CMD --wait --timeout 5m"

# Show diff (if helm-diff plugin is installed)
if helm plugin list | grep -q "diff"; then
    echo ""
    echo "📝 Changes to be applied:"
    if [ -n "$VALUES_FILE" ]; then
        helm diff upgrade "$RELEASE_NAME" "$CHART_DIR" -n "$NAMESPACE" -f "$VALUES_FILE" || true
    else
        helm diff upgrade "$RELEASE_NAME" "$CHART_DIR" -n "$NAMESPACE" || true
    fi
fi

# Confirm upgrade
echo ""
echo "Ready to upgrade with command:"
echo "  $HELM_CMD"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Upgrade cancelled"
    exit 1
fi

# Upgrade the chart
echo "🚀 Upgrading chart..."
eval "$HELM_CMD"

echo ""
echo "✅ Upgrade complete!"
echo ""
echo "📊 Check status:"
echo "  helm status $RELEASE_NAME -n $NAMESPACE"
echo ""
echo "🔍 View rollout status:"
echo "  kubectl rollout status deployment/$RELEASE_NAME-backend -n $NAMESPACE"
echo "  kubectl rollout status deployment/$RELEASE_NAME-frontend -n $NAMESPACE"
echo ""
echo "📝 View recent events:"
echo "  kubectl get events -n $NAMESPACE --sort-by='.lastTimestamp' | tail -20"
