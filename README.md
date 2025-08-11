<div align="center">
  <img src="logo.png" alt="VigilantRaccoon Logo" width="120" height="120">
  <h1>🦝 VigilantRaccoon</h1>
  <p><strong>Advanced Security Monitoring System for Linux Servers</strong></p>
  
  [![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![Flask](https://img.shields.io/badge/Flask-3.0+-lightgrey.svg)](https://flask.palletsprojects.com/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
  [![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](https://github.com/yourusername/VigilantRaccoon)
  [![Maintenance](https://img.shields.io/badge/Maintained-Yes-blue.svg)](https://github.com/yourusername/VigilantRaccoon/graphs/commit-activity)
  
  [![Security](https://img.shields.io/badge/Security-First-red.svg)](https://github.com/yourusername/VigilantRaccoon/security)
  [![SSH](https://img.shields.io/badge/SSH-Supported-orange.svg)](https://github.com/yourusername/VigilantRaccoon)
  [![Real-time](https://img.shields.io/badge/Real--time-Alerts-yellow.svg)](https://github.com/yourusername/VigilantRaccoon)
  [![Web UI](https://img.shields.io/badge/Web%20UI-Responsive-green.svg)](https://github.com/yourusername/VigilantRaccoon)
</div>

---

## 📋 Table of Contents

- [🚀 Features](#-features)
- [🛠️ Installation](#️-installation)
- [⚙️ Configuration](#️-configuration)
- [🔧 Usage](#-usage)
- [🏗️ Architecture](#️-architecture)
- [📊 API Reference](#-api-reference)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

---

## 🚀 Features

### 🔒 **Security Monitoring**
- **Real-time log collection** from Linux servers via SSH
- **Fail2Ban integration** with automatic ban detection
- **SSH authentication monitoring** (successful/failed logins)
- **PAM authentication failure detection**
- **Break-in attempt identification**

### 🌐 **Web Interface**
- **Modern, responsive dashboard** for security alerts
- **Real-time statistics** and filtering capabilities
- **Server management interface** (add/edit/delete)
- **Alert acknowledgment system** to prevent spam
- **Chronological sorting** and advanced filtering

### 📧 **Smart Notifications**
- **Immediate critical alerts** for urgent security events
- **Beautiful HTML email templates** with professional design
- **Configurable notification rules** and thresholds
- **Anti-spam filtering** for monitoring job logs

### 🏗️ **Clean Architecture**
- **Domain-driven design** with clear separation of concerns
- **Repository pattern** for data persistence
- **Use case layer** for business logic
- **Infrastructure abstraction** for external services

---

## 🛠️ Installation

### Prerequisites

- **Python 3.8+**
- **SSH access** to target Linux servers
- **SQLite** (included with Python)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/VigilantRaccoon.git
cd VigilantRaccoon

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data logs

# Copy and configure the configuration file
cp config.yaml.example config.yaml
# Edit config.yaml with your server details

# Run the application
python run.py
```

### Docker (Optional)

```bash
# Build the Docker image
docker build -t vigilant-raccoon .

# Run with Docker
docker run -p 8000:8000 -v $(pwd)/config.yaml:/app/config.yaml vigilant-raccoon
```

---

## ⚙️ Configuration

### Basic Configuration

```yaml
# config.yaml
servers:
  - name: web-server
    host: 192.168.1.100
    port: 22
    username: admin
    password: your_password
    logs:
      - journal:ssh
      - /var/log/fail2ban.log

email:
  enabled: true
  smtp_host: smtp.gmail.com
  smtp_port: 587
  use_tls: true
  username: your_email@gmail.com
  password: your_app_password
  from_addr: alerts@yourdomain.com
  to_addrs:
    - admin@yourdomain.com

web:
  host: "0.0.0.0"
  port: 8000
```

### Supported Log Sources

| Source | Description | OS Support |
|--------|-------------|------------|
| `journal:ssh` | Systemd SSH service logs | Debian/Ubuntu |
| `journal:sshd` | Systemd SSH service logs | RHEL/CentOS |
| `/var/log/auth.log` | Authentication logs | Debian/Ubuntu |
| `/var/log/secure` | Authentication logs | RHEL/CentOS |
| `/var/log/fail2ban.log` | Fail2Ban logs | All Linux |
| `ssh:auto` | Auto-detect best source | All Linux |

---

## 🔧 Usage

### Starting the Application

```bash
# Start the monitoring system
python run.py

# Access the web interface
open http://localhost:8000
```

### Web Interface

1. **Dashboard** (`/`) - Overview and navigation
2. **Security Alerts** (`/ui/alerts`) - View and manage security alerts
3. **Server Management** (`/ui/servers`) - Configure monitoring servers

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Application health check |
| `/alerts` | GET | List security alerts |
| `/servers` | GET/POST | Manage monitoring servers |
| `/logo.png` | GET | Application logo |

---

## 🏗️ Architecture

```
VigilantRaccoon/
├── domain/                 # Business entities and rules
│   ├── entities.py        # Alert, Server entities
│   └── repositories.py    # Abstract repository interfaces
├── use_cases/             # Business logic
│   └── detect_security_events.py
├── infrastructure/         # External services implementation
│   ├── persistence/       # SQLite repositories
│   ├── ssh/              # SSH client for log collection
│   └── notifiers/        # Email notification system
├── interfaces/            # Web interface
│   └── web/              # Flask web server
├── scheduler.py           # Background log collection
├── config.py             # Configuration management
└── run.py                # Application entry point
```

### Key Components

- **CollectorThread**: Background service for log collection
- **SSHLogClient**: SSH connection and log fetching
- **EmailNotifier**: Professional email notifications
- **SQLiteRepositories**: Data persistence layer

---

## 📊 API Reference

### Authentication

The application uses SSH key-based or password authentication for server access.

### Rate Limiting

- **Log collection**: Configurable interval (default: 60 seconds)
- **Email notifications**: Immediate for critical events, batched for regular alerts

### Error Handling

- **SSH connection failures**: Automatic retry with exponential backoff
- **Log parsing errors**: Graceful degradation with error logging
- **Database errors**: Transaction rollback and error reporting

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/yourusername/VigilantRaccoon.git
cd VigilantRaccoon

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest

# Run linting
flake8 .
```

### Code Style

- **Python**: PEP 8 compliance
- **Type hints**: Full type annotation support
- **Documentation**: Docstrings for all public methods
- **Testing**: Minimum 80% code coverage

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Paramiko** for SSH functionality
- **Flask** for the web framework
- **SQLite** for data persistence
- **Systemd** for modern Linux log management

---

## 📞 Support

- **Documentation**: [Wiki](https://github.com/yourusername/VigilantRaccoon/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/VigilantRaccoon/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/VigilantRaccoon/discussions)
- **Email**: support@yourdomain.com

---

<div align="center">
  <p><strong>Made with ❤️ for the security community</strong></p>
  
  [![GitHub stars](https://img.shields.io/github/stars/yourusername/VigilantRaccoon?style=social)](https://github.com/yourusername/VigilantRaccoon/stargazers)
  [![GitHub forks](https://img.shields.io/github/forks/yourusername/VigilantRaccoon?style=social)](https://github.com/yourusername/VigilantRaccoon/network)
  [![GitHub issues](https://img.shields.io/github/issues/yourusername/VigilantRaccoon)](https://github.com/yourusername/VigilantRaccoon/issues)
  [![GitHub pull requests](https://img.shields.io/github/issues-pr/yourusername/VigilantRaccoon)](https://github.com/yourusername/VigilantRaccoon/pulls)
  
  <p><em>Keep your servers safe with VigilantRaccoon! ��🔒</em></p>
</div>