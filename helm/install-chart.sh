#!/bin/bash
# Helper script to install the Helm chart with custom configuration

set -e

CHART_DIR="./airflow-health-dashboard"
RELEASE_NAME="${1:-airflow-health}"
NAMESPACE="${2:-airflow-health}"
VALUES_FILE="${3:-}"

echo "📦 Installing Airflow Health Dashboard"
echo "   Release: $RELEASE_NAME"
echo "   Namespace: $NAMESPACE"

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed. Please install Helm 3.x"
    exit 1
fi

# Create namespace if it doesn't exist
if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
    echo "📁 Creating namespace: $NAMESPACE"
    kubectl create namespace "$NAMESPACE"
else
    echo "✅ Namespace exists: $NAMESPACE"
fi

# Build helm install command
HELM_CMD="helm install $RELEASE_NAME $CHART_DIR --namespace $NAMESPACE"

if [ -n "$VALUES_FILE" ]; then
    if [ ! -f "$VALUES_FILE" ]; then
        echo "❌ Values file not found: $VALUES_FILE"
        exit 1
    fi
    echo "📋 Using values file: $VALUES_FILE"
    HELM_CMD="$HELM_CMD -f $VALUES_FILE"
else
    echo "⚠️  No values file specified, using default values"
    echo "   Tip: Create a custom values file and pass it as the 3rd argument"
fi

# Confirm installation
echo ""
echo "Ready to install with command:"
echo "  $HELM_CMD"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Installation cancelled"
    exit 1
fi

# Install the chart
echo "🚀 Installing chart..."
eval "$HELM_CMD"

echo ""
echo "✅ Installation complete!"
echo ""
echo "📊 Check status:"
echo "  helm status $RELEASE_NAME -n $NAMESPACE"
echo ""
echo "🔍 View pods:"
echo "  kubectl get pods -n $NAMESPACE"
echo ""
echo "📝 View logs:"
echo "  kubectl logs -f -l app.kubernetes.io/component=backend -n $NAMESPACE"
echo ""
echo "🌐 Access application (port-forward):"
echo "  kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME-frontend 3000:80"
echo "  kubectl port-forward -n $NAMESPACE svc/$RELEASE_NAME-backend 8000:8000"
