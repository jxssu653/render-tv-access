# TradingView Access Management System

A comprehensive Flask-based web application for managing TradingView Pine Script access through key-based authentication and real-time API integration.

## Features

- **Multi-tiered Authentication**: Admin and user roles with secure key-based access
- **Real TradingView Integration**: Direct API integration for Pine Script access management
- **Responsive Design**: Mobile-optimized interface with Bootstrap 5 dark theme
- **Database Management**: PostgreSQL support with SQLAlchemy ORM
- **Audit Logging**: Complete access tracking and management history
- **Deployment Ready**: Configured for Render cloud deployment

## Quick Start

### Local Development

1. **Clone and Setup**
   ```bash
   git clone <your-repo>
   cd tradingview-access-manager
   pip install -r render_requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your TradingView credentials
   ```

3. **Run Application**
   ```bash
   python main.py
   ```

4. **Access Application**
   - Open http://localhost:5000
   - Admin login: `admin@tradingview.com` / `admin123`

### Render Deployment

See [deploy_instructions.md](deploy_instructions.md) for complete deployment guide.

## System Architecture

### Backend
- **Flask**: Web framework with SQLAlchemy ORM
- **PostgreSQL**: Production database with connection pooling
- **TradingView API**: Real authentication and Pine Script management
- **Flask-Login**: Session management and user authentication

### Frontend
- **Bootstrap 5**: Responsive UI framework with dark theme
- **Vanilla JavaScript**: AJAX forms and real-time feedback
- **Font Awesome**: Icon library for enhanced UX

## Key Components

### Models
- **User**: Core user management with admin privileges
- **AccessKey**: One-time use keys for user registration
- **PineScript**: Pine Script configurations and metadata
- **UserAccess**: Junction table for user-script relationships
- **AccessLog**: Audit trail for all access operations

### API Endpoints
- `/api/validate-username`: TradingView username validation
- `/api/pine-scripts`: Available Pine Scripts listing
- `/api/grant-access`: Grant Pine Script access
- `/api/remove-access`: Remove Pine Script access

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TRADINGVIEW_USERNAME` | TradingView account username | Yes |
| `TRADINGVIEW_PASSWORD` | TradingView account password | Yes |
| `DATABASE_URL` | PostgreSQL connection string | Yes |
| `SESSION_SECRET` | Flask session secret key | Yes |
| `FLASK_ENV` | Environment (development/production) | No |
| `SESSION_TIMEOUT` | Session timeout in seconds | No |
| `LOG_LEVEL` | Logging level (DEBUG/INFO/WARNING/ERROR) | No |

## File Structure

```
├── app.py                 # Flask application setup
├── main.py               # Application entry point
├── routes.py             # Route definitions and API endpoints
├── models.py             # Database models
├── tradingview.py        # TradingView API integration
├── config.py             # Configuration management
├── templates/            # Jinja2 HTML templates
├── static/              # CSS, JavaScript, and images
├── render_requirements.txt # Python dependencies
├── render.yaml          # Render deployment configuration
├── deploy_instructions.md # Deployment guide
└── README.md            # This file
```

## Security Features

- Environment-based secrets management
- Session security with configurable keys
- Input validation and sanitization
- Audit logging for all operations
- CSRF protection and secure headers

## Mobile Optimization

- Responsive grid layouts for all screen sizes
- Touch-friendly interface elements
- Optimized form layouts for mobile input
- Collapsible navigation and compact views

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is private and proprietary. All rights reserved.

## Support

For deployment or technical issues:
1. Check the deployment logs
2. Verify environment variables
3. Validate TradingView credentials
4. Review the troubleshooting section in deploy_instructions.md