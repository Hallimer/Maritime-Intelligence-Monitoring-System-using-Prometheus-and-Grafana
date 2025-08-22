#!/bin/bash

# Maritime Intelligence Monitoring System - Setup Script
set -e

echo "🚢 Maritime Intelligence Monitoring System Setup"
echo "=================================================="

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed."
    echo "Please install Docker from https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is required but not installed."
    echo "Please install Docker Compose from https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose found"

# Create necessary directories
echo "📁 Creating directory structure..."
mkdir -p monitoring/prometheus/rules
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/provisioning/datasources
mkdir -p monitoring/grafana/provisioning/dashboards
mkdir -p data/sample_data
mkdir -p logs
mkdir -p docker

echo "✅ Directory structure created"

# Create Dockerfile for maritime exporter
echo "🐳 Creating Dockerfile for maritime exporter..."
cat > docker/Dockerfile.exporter << 'EOF'
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY monitoring/exporters/ ./
COPY data/ ./data/

# Create non-root user
RUN useradd -m -u 1000 maritime && chown -R maritime:maritime /app
USER maritime

EXPOSE 8000

CMD ["python", "maritime_exporter.py"]
EOF

# Create requirements.txt
echo "📦 Creating requirements.txt..."
cat > requirements.txt << 'EOF'
prometheus-client==0.17.1
requests==2.31.0
flask==2.3.3
numpy==1.24.3
pandas==1.5.3
python-dateutil==2.8.2
EOF

# Create environment file
echo "🔧 Creating environment configuration..."
cat > docker/.env << 'EOF'
# Maritime Intelligence Monitoring Environment
COMPOSE_PROJECT_NAME=maritime-intelligence

# Grafana Configuration
GF_SECURITY_ADMIN_USER=admin
GF_SECURITY_ADMIN_PASSWORD=admin
GF_USERS_ALLOW_SIGN_UP=false
GF_INSTALL_PLUGINS=grafana-worldmap-panel,grafana-piechart-panel

# Prometheus Configuration
PROMETHEUS_RETENTION_TIME=200h
PROMETHEUS_STORAGE_PATH=/prometheus

# Maritime Exporter Configuration
MARITIME_EXPORTER_PORT=8000
MARITIME_EXPORTER_LOG_LEVEL=INFO
MARITIME_VESSELS_COUNT=50
MARITIME_UPDATE_INTERVAL=300
EOF

# Copy configuration files to appropriate locations
echo "📋 Setting up configuration files..."

# Copy Prometheus config
cp prometheus.yml monitoring/prometheus/prometheus.yml 2>/dev/null || echo "⚠️  Please create prometheus.yml manually"

# Copy alert rules
cp maritime_alerts.yml monitoring/prometheus/rules/maritime_alerts.yml 2>/dev/null || echo "⚠️  Please create alert rules manually"

# Copy Grafana datasource config
cp grafana_datasource.yml monitoring/grafana/provisioning/datasources/prometheus.yml 2>/dev/null || echo "⚠️  Please create datasource config manually"

# Create Grafana dashboard provisioning config
cat > monitoring/grafana/provisioning/dashboards/dashboards.yml << 'EOF'
apiVersion: 1

providers:
  - name: 'Maritime Dashboards'
    orgId: 1
    folder: 'Maritime Intelligence'
    folderUid: maritime
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

# Create sample data generator script
echo "📊 Creating sample data generator..."
cat > scripts/generate_sample_data.sh << 'EOF'
#!/bin/bash
echo "🎲 Generating sample maritime data..."
python3 data/vessel_simulator.py --vessels 100 --duration 24 --output data/sample_data/
echo "✅ Sample data generated in data/sample_data/"
EOF

chmod +x scripts/generate_sample_data.sh

# Create cleanup script
echo "🧹 Creating cleanup script..."
mkdir -p scripts
cat > scripts/cleanup.sh << 'EOF'
#!/bin/bash
echo "🧹 Cleaning up Maritime Intelligence Monitoring System..."
docker-compose -f docker/docker-compose.yml down -v
docker system prune -f
echo "✅ Cleanup complete"
EOF

chmod +x scripts/cleanup.sh

# Create quick start script
cat > scripts/start.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Maritime Intelligence Monitoring System..."
docker-compose -f docker/docker-compose.yml up -d
echo "✅ System started!"
echo ""
echo "🌐 Access URLs:"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - Prometheus: http://localhost:9090"
echo "   - Maritime Exporter: http://localhost:8000/metrics"
echo ""
echo "⏳ Please wait 2-3 minutes for all services to be ready"
EOF

chmod +x scripts/start.sh

# Final setup instructions
echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "📁 Project structure created with:"
echo "   - Docker Compose configuration"
echo "   - Prometheus monitoring setup"
echo "   - Grafana dashboards"
echo "   - Custom maritime data exporter"
echo "   - Alert rules for maritime operations"
echo ""
echo "🚀 To start the system:"
echo "   ./scripts/start.sh"
echo ""
echo "🌐 Once running, access:"
echo "   - Grafana: http://localhost:3000 (admin/admin)"
echo "   - Prometheus: http://localhost:9090"
echo "   - Maritime Metrics: http://localhost:8000/metrics"
echo ""
echo "📖 Next steps:"
echo "   1. Start the system with ./scripts/start.sh"
echo "   2. Import Grafana dashboards from monitoring/grafana/dashboards/"
echo "   3. Configure alerts in Prometheus"
echo "   4. Customize vessel simulation parameters"
echo ""
echo "🆘 For help:"
echo "   - Check logs: docker-compose logs -f"
echo "   - Cleanup: ./scripts/cleanup.sh"
echo ""
echo "📊 This setup demonstrates:"
echo "   ✅ Real-time maritime data collection"
echo "   ✅ Custom Prometheus exporters"
echo "   ✅ Business intelligence dashboards"
echo "   ✅ Operational alerting"
echo "   ✅ Scalable monitoring architecture"