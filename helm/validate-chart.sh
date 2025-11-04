#!/bin/bash
# Helper script to validate and test the Helm chart

set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CHART_DIR="$SCRIPT_DIR/airflow-health-dashboard"
CHART_NAME="airflow-health-dashboard"

echo "🔍 Validating Helm chart..."

# Check if helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed. Please install Helm 3.x"
    exit 1
fi

echo "✅ Helm version:"
helm version --short

# Lint the chart
echo ""
echo "📋 Linting chart..."
helm lint "$CHART_DIR"

# Test template rendering with default values
echo ""
echo "🎨 Testing template rendering (default values)..."
helm template test-release "$CHART_DIR" > /dev/null
echo "✅ Default values template OK"

# Test template rendering with production values
if [ -f "$CHART_DIR/values-production.yaml" ]; then
    echo ""
    echo "🎨 Testing template rendering (production values)..."
    helm template test-release "$CHART_DIR" -f "$CHART_DIR/values-production.yaml" > /dev/null
    echo "✅ Production values template OK"
fi

# Test template rendering with dev values
if [ -f "$CHART_DIR/values-dev.yaml" ]; then
    echo ""
    echo "🎨 Testing template rendering (dev values)..."
    helm template test-release "$CHART_DIR" -f "$CHART_DIR/values-dev.yaml" > /dev/null
    echo "✅ Dev values template OK"
fi

# Test dry-run installation
echo ""
echo "🧪 Testing dry-run installation..."
helm install test-release "$CHART_DIR" --dry-run --debug > /dev/null
echo "✅ Dry-run installation OK"

# Validate YAML syntax
echo ""
echo "📝 Validating YAML syntax..."
helm template test-release "$CHART_DIR" | kubectl apply --dry-run=client -f - > /dev/null 2>&1
echo "✅ YAML syntax valid"

echo ""
echo "✅ All validations passed!"
echo ""
echo "To install the chart, run:"
echo "  helm install my-release $CHART_DIR"
