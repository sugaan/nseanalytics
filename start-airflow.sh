#!/bin/bash

echo "🚀 Starting Airflow for NSE/BSE Announcements Project"
echo "=================================================="

# Set permissions
echo "Setting permissions..."
mkdir -p airflow/logs airflow/dags airflow/plugins data exports
chmod -R 777 airflow data exports

# Set Airflow UID
echo "AIRFLOW_UID=$(id -u)" > .env
echo "_AIRFLOW_WWW_USER_USERNAME=admin" >> .env
echo "_AIRFLOW_WWW_USER_PASSWORD=admin123" >> .env

# Initialize Airflow
echo "Initializing Airflow..."
docker-compose up airflow-init

# Start services
echo "Starting Airflow services..."
docker-compose up -d

echo ""
echo "✅ Airflow is starting!"
echo "=================================================="
echo "🌐 Web UI: http://localhost:8080"
echo "👤 Username: admin"
echo "🔑 Password: admin123"
echo ""
echo "Waiting for services to be healthy (30 seconds)..."
sleep 30

docker-compose ps

echo ""
echo "📝 View logs:"
echo "  docker-compose logs -f airflow-scheduler"
echo "  docker-compose logs -f airflow-webserver"
echo ""
echo "🛑 Stop Airflow:"
echo "  docker-compose down"
