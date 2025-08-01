# TradingView Access Management System

## Overview

This is a comprehensive Flask-based web application with advanced key-based authentication for managing TradingView Pine Script access. The system features a multi-tiered interface: admin panel for creating and managing access keys, user registration workflow through key validation, and comprehensive access control with one-user-per-account restrictions until full removal.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web framework with SQLAlchemy ORM and Flask-Login for authentication
- **Database**: PostgreSQL with connection pooling and health checks
- **Authentication**: Key-based access control with Flask-Login session management
- **User Management**: Multi-tiered access system (admin/user roles)
- **Session Management**: Flask sessions with proxy fix for deployment environments
- **Configuration**: Environment-based configuration with dotenv support
- **TradingView Integration**: Real authentication with session management and Pine Script access control

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask
- **CSS Framework**: Bootstrap 5 with dark theme (Replit-themed)
- **JavaScript**: Vanilla JavaScript with Bootstrap components and AJAX for form handling
- **Icons**: Font Awesome for UI icons
- **User Experience**: Multi-page authentication flow with real-time feedback

## Key Components

### Models (models.py)
- **User**: Core user model with Flask-Login integration, admin flags, and TradingView username tracking
- **AccessKey**: One-time use access keys created by admins for user registration
- **AccessLog**: Tracks all access management operations with timestamps, status, and user attribution
- **PineScript**: Stores Pine Script configurations including ID, name, description, and active status
- **UserAccess**: Junction table tracking which users have access to which Pine Scripts

### Routes (routes.py)
- **Home Route** (`/`): Key entry portal for new users or login link for existing users
- **Key Validation** (`/validate-key`): Validates access keys and initiates registration flow
- **Registration** (`/register`): User account creation after key validation
- **Login/Logout** (`/login`, `/logout`): Standard authentication endpoints
- **Management Route** (`/manage`): User access management interface for granting/removing access
- **Admin Panel** (`/admin`): Comprehensive admin interface for key creation and user management
- **API Endpoints**: RESTful APIs for username validation, Pine Script management, and access control

### TradingView Integration (tradingview.py)
- **TradingViewAPI Class**: Handles authentication and session management with TradingView
- **Session Persistence**: Saves and loads sessions to/from file for efficiency
- **Cookie Management**: Manages TradingView authentication cookies

### Configuration (config.py)
- **Environment Variables**: Manages TradingView credentials and system settings
- **Validation**: Ensures required configuration is present
- **Defaults**: Provides sensible defaults for optional settings

## Data Flow

1. **User Authentication**: System authenticates with TradingView using stored credentials
2. **Session Management**: Sessions are cached locally to avoid repeated authentication
3. **Access Operations**: Users can grant or remove access to Pine Scripts through the web interface
4. **Logging**: All operations are logged to the database for audit purposes
5. **Status Monitoring**: Dashboard provides real-time status of operations and system health

## External Dependencies

### Required Environment Variables
- `TRADINGVIEW_USERNAME`: TradingView account username
- `TRADINGVIEW_PASSWORD`: TradingView account password
- `DATABASE_URL`: Database connection string (optional, defaults to SQLite)
- `SESSION_SECRET`: Flask session secret key (optional, has development default)

### Optional Configuration
- `SESSION_TIMEOUT`: Session timeout in seconds (default: 3600)
- `DEFAULT_PINE_IDS`: Comma-separated list of default Pine Script IDs
- `LOG_LEVEL`: Logging level (default: INFO)

### Third-Party Services
- **TradingView**: Primary integration for managing Pine Script access
- **Bootstrap CDN**: For UI styling and components
- **Font Awesome CDN**: For icons

## Deployment Strategy

### Local Development
- Runs on Flask development server (port 5000)
- Uses SQLite database for simplicity
- Debug mode enabled for development

### Production Considerations
- ProxyFix middleware configured for reverse proxy deployments
- Database connection pooling with health checks
- Environment-based configuration for security
- Session file persistence for TradingView authentication

### Database Strategy
- SQLAlchemy with declarative base for easy model management
- Database tables created automatically on application startup
- Connection pooling and health checks configured for reliability

### Security Features
- Environment-based secrets management
- Session security with configurable secret keys
- Input validation for user data
- Audit logging for all access operations

## Key Design Decisions

### Database Choice
- **Problem**: Need persistent storage for logs and Pine Script configurations
- **Solution**: SQLAlchemy with SQLite default, PostgreSQL support via environment variables
- **Rationale**: SQLite for development simplicity, easy migration to PostgreSQL for production

### Session Management
- **Problem**: Avoid repeated TradingView authentication for efficiency
- **Solution**: File-based session persistence with cookie management
- **Rationale**: Reduces API calls and improves user experience

### Configuration Management
- **Problem**: Secure handling of TradingView credentials
- **Solution**: Environment variable configuration with validation
- **Rationale**: Follows 12-factor app principles for configuration management

### UI Framework
- **Problem**: Need responsive, professional interface
- **Solution**: Bootstrap 5 with dark theme and Font Awesome icons
- **Rationale**: Rapid development with consistent, modern UI components

### Pine Script Management
- **Problem**: Deactivated Pine Scripts caused re-adding issues
- **Solution**: Complete removal from backend when turned off instead of soft deletion
- **Rationale**: Prevents database conflicts and allows clean re-addition of scripts
- **Date**: July 20, 2025

### Real TradingView API Integration
- **Problem**: Demo mode was not performing actual access management
- **Solution**: Implemented real TradingView API endpoints (username_hint, pine_perm/add, pine_perm/list_users, pine_perm/remove)
- **Rationale**: Provides genuine Pine Script access control with proper authentication
- **Date**: July 20, 2025

## Recent Changes

### Data Persistence and Backup System - July 20, 2025
- **Comprehensive Backup System**: Implemented `backup_system.py` with automatic and manual backup functionality
  - Auto-backup on application startup to prevent data loss
  - Manual backup creation with custom naming
  - Complete JSON export of all database tables with relationships
  - Backup restoration with data validation and integrity checks
  - Automatic cleanup of old backups (keeps last 10 auto-backups)
- **Data Recovery System**: Created `data_recovery.py` for data integrity and recovery
  - Database health checks with comprehensive status reporting
  - Data validation and automatic fixing of orphaned records
  - Default data recovery (admin user, Pine Scripts) if missing
  - Integrity validation for foreign key relationships
- **Admin Data Management Panel**: Enhanced admin interface with data management tools
  - "Create Backup" button for manual backups
  - "Health Check" for real-time database status
  - "Validate Data" for integrity checks and fixes
  - Visual status indicators for backup and health status
- **Command Line Tools**: Added `data_manager.py` for server-side data management
  - Backup creation, restoration, and listing via CLI
  - Health checks and data validation from command line
  - Recovery operations for maintenance and troubleshooting
- **PostgreSQL Integration**: Enhanced database configuration for production reliability
  - Connection pooling and health checks configured
  - Automatic database table creation on startup
  - Environment-based database URL configuration with Render compatibility

### Mobile Optimization and Render Deployment Setup - July 20, 2025
- **Mobile View Optimization**: Enhanced CSS with responsive breakpoints for mobile devices, improved form layouts and card responsiveness
- **Access Generation Fix**: Improved error handling and logging for TradingView API integration with detailed status tracking
- **Render Deployment**: Created complete deployment configuration for Render platform including:
  - `render_requirements.txt`: Python dependencies for Render deployment
  - `render.yaml`: Service configuration with web service and PostgreSQL database setup
  - `Procfile`: Process configuration for web service startup
  - `deploy_instructions.md`: Complete step-by-step deployment guide
  - `secrets_to_env.py`: Script to transfer environment variables to .env file
  - Database URL fix for Render PostgreSQL compatibility (postgres:// to postgresql://)
- **Environment Configuration**: Added .env.example template and production environment support
- **Admin Panel Mobile**: Optimized admin interface layout for mobile devices with responsive grid classes
- **Port Configuration**: Updated main.py to dynamically use PORT environment variable for Render compatibility
- **SQLAlchemy Compatibility Fix**: Resolved Python 3.13+ compatibility issues by:
  - Updated SQLAlchemy to version 2.0.32
  - Set Python runtime to 3.11.9 in runtime.txt
  - Created fix_render_deployment.py script for automated troubleshooting
  - Enhanced deployment instructions with troubleshooting section