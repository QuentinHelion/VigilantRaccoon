# Log Rotation System

VigilantRaccoon includes a configurable daily log rotation system that automatically manages log files to prevent disk space issues while maintaining audit trails.

## Features

- **Daily Rotation**: Logs are automatically rotated at midnight each day
- **Configurable Retention**: Default 30-day retention, fully configurable
- **Automatic Cleanup**: Old log files are automatically removed based on retention settings
- **Backward Compatibility**: Falls back to size-based rotation when daily rotation is disabled
- **Professional Format**: Rotated log files use clear date-based naming (e.g., `app.log.2024-01-15`)

## Configuration

### Basic Settings

In your `config.yaml`, configure the logging section:

```yaml
logging:
  level: INFO                    # Log level (DEBUG, INFO, WARNING, ERROR)
  file_path: ./logs/app.log      # Main log file path
  daily_rotation: true           # Enable daily rotation
  retention_days: 30             # Keep logs for 30 days
  console: true                  # Also log to console
```

### Advanced Settings

You can also configure legacy size-based rotation as a fallback:

```yaml
logging:
  daily_rotation: false          # Disable daily rotation
  max_bytes: 1000000            # 1 MB per log file
  backup_count: 3                # Keep 3 backup files
```

## How It Works

### Daily Rotation

When `daily_rotation: true`:

1. **Automatic Rotation**: Logs are rotated at midnight each day
2. **File Naming**: Rotated files use the format `app.log.YYYY-MM-DD`
3. **Retention**: Files older than `retention_days` are automatically deleted
4. **Current Log**: The main `app.log` file continues to receive new log entries

### Fallback Rotation

When `daily_rotation: false`:

1. **Size-based**: Logs are rotated when they reach `max_bytes`
2. **Backup Count**: Keeps up to `backup_count` backup files
3. **File Naming**: Uses the format `app.log.1`, `app.log.2`, etc.

## File Structure

```
logs/
├── app.log                    # Current log file
├── app.log.2024-01-15        # Yesterday's log
├── app.log.2024-01-14        # Day before yesterday
├── app.log.2024-01-13        # 3 days ago
└── .gitkeep                  # Git tracking file
```

## Management

### Automatic Management

The system automatically:
- Rotates logs daily at midnight
- Removes files older than the retention period
- Maintains the current log file for new entries

### Manual Management

You can manually manage logs using the utility script:

```bash
# Show log statistics
python utils/log_rotation.py --stats

# Manually rotate logs
python utils/log_rotation.py --rotate

# Clean up old logs
python utils/log_rotation.py --cleanup

# Preview cleanup without deleting
python utils/log_rotation.py --cleanup --dry-run
```

## Best Practices

### Production Deployment

1. **Set Appropriate Retention**: 30 days is usually sufficient for most use cases
2. **Monitor Disk Space**: Ensure sufficient space for log retention
3. **Disable Console Logging**: Set `console: false` in production
4. **Regular Monitoring**: Check log rotation is working correctly

### Development

1. **Enable Console Logging**: Set `console: true` for development
2. **Shorter Retention**: Use shorter retention periods during development
3. **Manual Rotation**: Use manual rotation for testing

## Troubleshooting

### Common Issues

1. **Log File in Use**: Cannot rotate logs while application is running
   - Solution: Stop the application before manual rotation
   - Automatic rotation works while running

2. **Permission Errors**: Cannot write to log directory
   - Solution: Check directory permissions and ownership

3. **Disk Space**: Logs consuming too much space
   - Solution: Reduce retention period or enable daily rotation

### Monitoring

Check log rotation status:

```bash
python utils/log_rotation.py --stats
```

Look for:
- Correct number of log files
- Appropriate file sizes
- Recent rotation dates
- No files older than retention period

## Configuration Examples

### Minimal Configuration

```yaml
logging:
  level: INFO
  file_path: ./logs/app.log
  daily_rotation: true
  retention_days: 30
```

### Production Configuration

```yaml
logging:
  level: WARNING
  file_path: /var/log/vigilant_raccoon/app.log
  daily_rotation: true
  retention_days: 90
  console: false
```

### Development Configuration

```yaml
logging:
  level: DEBUG
  file_path: ./logs/app.log
  daily_rotation: true
  retention_days: 7
  console: true
```

## Migration from Size-based Rotation

If you're upgrading from the old size-based rotation:

1. **Backup Configuration**: Save your current `config.yaml`
2. **Enable Daily Rotation**: Set `daily_rotation: true`
3. **Set Retention**: Configure `retention_days` as needed
4. **Test**: Verify rotation works correctly
5. **Cleanup**: Remove old size-based settings if desired

The system maintains backward compatibility, so you can always revert to size-based rotation by setting `daily_rotation: false`.
