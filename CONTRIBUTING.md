# Contributing to VigilantRaccoon

Thank you for your interest in contributing to VigilantRaccoon! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites
- Python 3.8+
- Git
- SSH access to test servers (for testing)

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/yourusername/VigilantRaccoon.git
   cd VigilantRaccoon
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Setup configuration**
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your test server details
   ```

5. **Run tests**
   ```bash
   python run_tests.py all
   ```

## Development Guidelines

### Code Style
- **Python**: Follow PEP 8 style guide
- **Type hints**: Use type annotations for all public methods
- **Documentation**: Add docstrings for all public methods
- **Line length**: Maximum 120 characters
- **Imports**: Group imports (standard library, third-party, local)

### Architecture Principles
- **Domain-driven design**: Keep business logic in use cases
- **Repository pattern**: Use repositories for data access
- **Dependency injection**: Inject dependencies through constructors
- **Single responsibility**: Each class should have one reason to change
- **Open/closed principle**: Open for extension, closed for modification

### Testing
- **Coverage**: Maintain minimum 80% code coverage
- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **Test naming**: Use descriptive test names that explain the scenario

### Git Workflow
1. **Create feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and commit**
   ```bash
   git add .
   git commit -m "feat: add new security monitoring feature"
   ```

3. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Commit Message Format
Use conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

## Project Structure

```
VigilantRaccoon/
├── domain/                 # Business entities and rules
│   ├── entities.py        # Alert, Server entities
│   └── repositories.py    # Abstract repository interfaces
├── use_cases/             # Business logic
│   ├── detect_security_events.py
│   └── process_monitoring.py
├── infrastructure/         # External services implementation
│   ├── persistence/       # SQLite repositories
│   ├── ssh/              # SSH client for log collection
│   └── notifiers/        # Email notification system
├── interfaces/            # Web interface
│   └── web/              # Flask web server
├── templates/             # HTML templates
├── tests/                 # Test suite
├── docs/                  # Documentation
├── scheduler.py           # Background log collection
├── config.py             # Configuration management
└── run.py                # Application entry point
```

## Adding New Features

### 1. Security Monitoring Rules
- Add rule logic in `use_cases/detect_security_events.py`
- Create corresponding tests in `tests/test_detect_security_events.py`
- Update documentation with rule description

### 2. New Alert Types
- Extend `domain/entities.py` with new alert fields
- Update database schema in repositories
- Add migration scripts if needed

### 3. Web Interface Features
- Add routes in `interfaces/web/server.py`
- Create HTML templates in `templates/`
- Add JavaScript functionality as needed
- Update navigation in `templates/layout.html`

### 4. Configuration Options
- Extend `config.py` with new configuration classes
- Update `config.yaml.example` with examples
- Add validation logic

## Testing

### Running Tests
```bash
# Run all tests
python run_tests.py all

# Run specific test
python run_tests.py config

# List available tests
python run_tests.py list

# Run with pytest directly
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

### Test Structure
- **Unit tests**: Test individual functions and methods
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows
- **Mock external dependencies**: Use unittest.mock for SSH, email, etc.

### Test Data
- Use fixtures for common test data
- Create test databases in memory
- Mock external services (SSH, SMTP)
- Clean up test data after each test

## Documentation

### Code Documentation
- Use docstrings for all public methods
- Follow Google docstring format
- Include examples for complex methods
- Document exceptions and error conditions

### User Documentation
- Update README.md for new features
- Add configuration examples
- Document API endpoints
- Include troubleshooting guides

### Developer Documentation
- Document architecture decisions
- Explain design patterns used
- Provide setup and development guides
- Include contribution guidelines

## Security Considerations

### Input Validation
- Validate all user inputs
- Sanitize data before database storage
- Use parameterized queries to prevent SQL injection
- Validate file paths and prevent directory traversal

### Authentication & Authorization
- Implement proper authentication for web interface
- Use secure session management
- Validate SSH keys and passwords
- Implement rate limiting for API endpoints

### Data Protection
- Encrypt sensitive configuration data
- Secure database connections
- Implement proper logging without exposing sensitive data
- Use HTTPS for web interface

## Performance

### Database Optimization
- Use appropriate indexes
- Optimize queries for large datasets
- Implement connection pooling
- Use transactions for data consistency

### Memory Management
- Avoid memory leaks in long-running processes
- Use generators for large data sets
- Implement proper cleanup in destructors
- Monitor memory usage in production

### Scalability
- Design for horizontal scaling
- Use async operations where appropriate
- Implement caching strategies
- Monitor performance metrics

## Deployment

### Docker
- Update Dockerfile for new dependencies
- Test docker-compose configuration
- Ensure proper environment variable handling
- Test container health checks

### Production Considerations
- Use production-grade web server (nginx, gunicorn)
- Implement proper logging and monitoring
- Use environment-specific configurations
- Implement backup and recovery procedures

## Getting Help

### Communication Channels
- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas
- **Pull Requests**: Submit code changes
- **Email**: support@qhelion.fr

### Before Submitting Issues
1. Check existing issues and discussions
2. Search documentation for solutions
3. Test with latest version
4. Provide detailed reproduction steps
5. Include system information and logs

### Code Review Process
1. Submit pull request with clear description
2. Ensure all tests pass
3. Update documentation as needed
4. Respond to review comments promptly
5. Maintain clean commit history

## Recognition

Contributors will be recognized in:
- Project README
- Release notes
- Contributor hall of fame
- GitHub contributors list

Thank you for contributing to VigilantRaccoon!
