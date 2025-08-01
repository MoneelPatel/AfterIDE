# Setup

This directory contains setup and environment configuration files for the AfterIDE project.

## Files

- **env.example** - Example environment variables file that should be copied to `.env` and configured

## Usage

### Setting up Environment Variables
```bash
cd setup
cp env.example ../.env
# Edit ../.env with your specific configuration
```

## Notes

The environment file contains configuration for database connections, API keys, and other environment-specific settings. Make sure to never commit the actual `.env` file to version control. 