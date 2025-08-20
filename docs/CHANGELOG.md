# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-01-XX

### Added
- **Process Monitoring**: Real-time monitoring of system processes, network connections, and file activities
- **Web Interface**: Dedicated process monitoring page with real-time alerts and statistics
- **API Endpoints**: New `/api/process-monitoring` endpoint for process monitoring alerts
- **Daily Log Rotation**: Configurable daily log rotation system with automatic retention management
  - Default 30-day retention period (configurable)
  - Automatic daily rotation at midnight
  - Fallback to size-based rotation when daily rotation is disabled
  - Log rotation utility script for manual management and cleanup
- **Email Notifications**: Enhanced email system with critical alert and daily report capabilities
- **Documentation**: Comprehensive CHANGELOG and CONTRIBUTING guides

### Changed
- **Configuration**: Restructured `config.yaml` with cleaner organization and better examples
- **Logging System**: Enhanced logging configuration with daily rotation support
- **UI/UX**: Removed all emojis for cleaner, more professional appearance
- **CSS Architecture**: Centralized all styles in external CSS file for better maintainability and performance
- **Internationalization**: Translated all French text to English throughout the codebase

### Removed
- **Emojis**: All emoji characters removed from UI and code for professional appearance
- **French Text**: All French language content translated to English
- **Temporary Files**: Cleaned up test scripts and temporary development files
- **Redundant Documentation**: Consolidated duplicate documentation files

### Fixed
- **Process Monitoring Display**: Resolved issue where process monitoring logs weren't appearing in web interface
- **Configuration Issues**: Fixed localhost configuration for process monitoring functionality
- **Database Access**: Improved database querying and error handling

### Security
- **Process Monitoring**: Enhanced security through real-time process and network activity monitoring
- **SSH Authentication**: Improved SSH key-based authentication for remote log collection
- **Input Validation**: Enhanced input validation and sanitization

### Documentation
- **API Documentation**: Added comprehensive API endpoint documentation
- **Configuration Guide**: Enhanced configuration examples and documentation
- **Contributing Guidelines**: Added detailed contribution and development guidelines
- **Process Monitoring Guide**: Comprehensive documentation for the new monitoring features

### Technical Details
- **Log Rotation**: Uses `TimedRotatingFileHandler` for daily rotation with configurable retention
- **Backward Compatibility**: Maintains support for existing size-based rotation configuration
- **Utility Scripts**: Added `utils/log_rotation.py` for log management operations
- **Testing**: Enhanced test coverage for new logging functionality
