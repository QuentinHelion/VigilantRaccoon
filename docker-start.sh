#!/bin/bash

# VigilantRaccoon Docker Startup Script

set -e

echo "🚀 Starting VigilantRaccoon with Docker..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose is not installed. Please install it first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data logs ssl

# Check if SSL certificates exist
if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
    echo "⚠️  SSL certificates not found. Creating self-signed certificates..."
    mkdir -p ssl
    openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes -subj "/C=FR/ST=State/L=City/O=Organization/CN=localhost"
    echo "✅ Self-signed SSL certificates created."
fi

# Check if config.yaml exists
if [ ! -f "config.yaml" ]; then
    echo "⚠️  config.yaml not found. Creating from example..."
    if [ -f "config.yaml.example" ]; then
        cp config.yaml.example config.yaml
        echo "✅ config.yaml created from example. Please edit it with your settings."
    else
        echo "❌ config.yaml.example not found. Please create config.yaml manually."
        exit 1
    fi
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
if docker-compose ps | grep -q "healthy"; then
    echo "✅ All services are healthy!"
else
    echo "⚠️  Some services may not be fully ready yet."
fi

echo ""
echo "🎉 VigilantRaccoon is starting up!"
echo ""
echo "📊 Web Interface: http://localhost:8000"
echo "🔒 Secure Web Interface: https://localhost (if using nginx)"
echo "📚 API Documentation: http://localhost:8000/alerts"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f vigilant-raccoon"
echo "  Stop services: docker-compose down"
echo "  Restart services: docker-compose restart"
echo "  Update and restart: docker-compose up --build -d"
echo ""
echo "🔍 Check service status: docker-compose ps"
