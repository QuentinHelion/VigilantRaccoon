# 🐳 Docker Deployment Guide

This guide covers deploying VigilantRaccoon using Docker and Docker Compose.

## 📋 Prerequisites

- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later
- **OpenSSL**: For SSL certificate generation (optional)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/yourusername/vigilant-raccoon.git
cd vigilant-raccoon
```

### 2. Configure the Application

```bash
# Copy and edit the configuration
cp config.yaml.example config.yaml
nano config.yaml  # or use your preferred editor
```

**Important**: Update the following in `config.yaml`:
- Server credentials (hosts, usernames, passwords)
- Email settings (SMTP server, credentials, recipients)
- Web interface host: use `"0.0.0.0"` for Docker

### 3. Start with Docker

```bash
# Make the startup script executable
chmod +x docker-start.sh

# Run the startup script (recommended)
./docker-start.sh

# Or manually with docker-compose
docker-compose up --build -d
```

### 4. Access the Application

- **Web Interface**: http://localhost:8000
- **Secure Interface**: https://localhost (with nginx)
- **API**: http://localhost:8000/alerts

## 🏗️ Architecture

The Docker setup includes:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │ VigilantRaccoon │    │   SQLite DB     │
│   (Port 80/443) │◄──►│   (Port 8000)   │◄──►│   (./data/)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Services

1. **vigilant-raccoon**: Main application container
   - Python 3.11-slim base image
   - SSH client for log collection
   - Web interface and API
   - Background log collection

2. **nginx**: Reverse proxy (optional)
   - SSL/TLS termination
   - Rate limiting
   - Security headers
   - Gzip compression

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | `1` | Ensures Python output is not buffered |

### Volume Mounts

| Host Path | Container Path | Description |
|-----------|----------------|-------------|
| `./config.yaml` | `/app/config.yaml` | Application configuration |
| `./data` | `/app/data` | SQLite database and persistent data |
| `./logs` | `/app/logs` | Application logs |
| `~/.ssh` | `/home/vigilant/.ssh` | SSH keys for server access |

### Ports

| Service | Host Port | Container Port | Description |
|---------|-----------|----------------|-------------|
| vigilant-raccoon | 8000 | 8000 | Web interface and API |
| nginx | 80, 443 | 80, 443 | HTTP/HTTPS proxy |

## 🔒 SSL/TLS Configuration

### Automatic Self-Signed Certificates

The startup script automatically generates self-signed SSL certificates:

```bash
# Certificates are stored in ./ssl/
ssl/
├── cert.pem    # SSL certificate
└── key.pem     # Private key
```

### Using Real Certificates

Replace the self-signed certificates with real ones:

```bash
# Copy your certificates
cp /path/to/your/cert.pem ssl/cert.pem
cp /path/to/your/key.pem ssl/key.pem

# Restart nginx
docker-compose restart nginx
```

## 📊 Monitoring and Health Checks

### Health Check Endpoint

```bash
# Check application health
curl http://localhost:8000/health

# Check Docker container health
docker-compose ps
```

### Logs

```bash
# View application logs
docker-compose logs -f vigilant-raccoon

# View nginx logs
docker-compose logs -f nginx

# View all logs
docker-compose logs -f
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Port Already in Use

```bash
# Check what's using the port
sudo netstat -tulpn | grep :8000

# Stop conflicting services or change ports in docker-compose.yml
```

#### 2. Permission Denied

```bash
# Fix SSH key permissions
chmod 600 ~/.ssh/id_rsa
chmod 644 ~/.ssh/id_rsa.pub

# Fix directory permissions
sudo chown -R $USER:$USER data/ logs/
```

#### 3. Database Connection Issues

```bash
# Check database file permissions
ls -la data/

# Recreate database (WARNING: data loss)
rm data/vigilant_raccoon.db
docker-compose restart vigilant-raccoon
```

#### 4. Email Not Working

```bash
# Check email configuration
docker-compose exec vigilant-raccoon cat /app/config.yaml

# Check application logs for email errors
docker-compose logs vigilant-raccoon | grep -i email
```

### Debug Mode

```bash
# Run in debug mode
docker-compose down
docker-compose run --rm vigilant-raccoon python run.py --debug

# Or modify config.yaml
logging:
  level: DEBUG
  console: true
```

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose down
docker-compose up --build -d
```

### Backup and Restore

```bash
# Backup database
docker-compose exec vigilant-raccoon cp /app/data/vigilant_raccoon.db /app/data/backup_$(date +%Y%m%d_%H%M%S).db

# Backup configuration
cp config.yaml config.yaml.backup

# Restore from backup
cp config.yaml.backup config.yaml
docker-compose restart vigilant-raccoon
```

### Scaling

For production deployments, consider:

```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  vigilant-raccoon:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
    restart_policy:
      condition: on-failure
      delay: 5s
      max_attempts: 3
```

## 🛡️ Security Considerations

### Production Hardening

1. **Use real SSL certificates** instead of self-signed ones
2. **Restrict SSH key access** to monitoring servers only
3. **Enable firewall rules** to restrict access to necessary ports
4. **Regular security updates** for base images
5. **Monitor container logs** for suspicious activity

### Network Security

```bash
# Restrict nginx to specific IPs (optional)
# Edit nginx.conf to add allow/deny rules
location / {
    allow 192.168.1.0/24;
    deny all;
    proxy_pass http://vigilant_backend;
}
```

## 📚 Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Configuration](https://nginx.org/en/docs/)
- [SSL/TLS Best Practices](https://ssl-config.mozilla.org/)

---

**Need help?** Check the [main README](../README.md) or open an [issue](https://github.com/yourusername/vigilant-raccoon/issues).
