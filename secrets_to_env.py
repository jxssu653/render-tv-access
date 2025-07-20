#!/usr/bin/env python3
"""
Script to transfer environment variables to .env file for Render deployment
"""
import os

def create_env_file():
    """Create .env file with current environment variables"""
    env_vars = {
        'TRADINGVIEW_USERNAME': os.getenv('TRADINGVIEW_USERNAME', ''),
        'TRADINGVIEW_PASSWORD': os.getenv('TRADINGVIEW_PASSWORD', ''),
        'SESSION_SECRET': os.getenv('SESSION_SECRET', 'your-secret-key-here'),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'sqlite:///tradingview_access.db'),
        'FLASK_ENV': 'production',
        'PYTHONUNBUFFERED': '1',
        'SESSION_TIMEOUT': '3600',
        'LOG_LEVEL': 'INFO'
    }
    
    with open('.env', 'w') as f:
        f.write("# TradingView Access Manager Environment Variables\n")
        f.write("# Generated for Render deployment\n\n")
        
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print("✅ Created .env file with environment variables")
    print("📝 Remember to set these environment variables in Render dashboard:")
    for key, value in env_vars.items():
        if key in ['TRADINGVIEW_USERNAME', 'TRADINGVIEW_PASSWORD'] and value:
            print(f"  - {key}: [SET IN RENDER]")
        else:
            print(f"  - {key}: {value}")

if __name__ == "__main__":
    create_env_file()