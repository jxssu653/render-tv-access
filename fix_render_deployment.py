#!/usr/bin/env python3
"""
Fix script for Render deployment issues
Addresses common problems like SQLAlchemy compatibility and Python version issues
"""
import os
import sys

def check_python_version():
    """Check if Python version is compatible"""
    major, minor = sys.version_info[:2]
    print(f"Current Python version: {major}.{minor}")
    
    if major == 3 and minor >= 13:
        print("⚠️  WARNING: Python 3.13+ may have SQLAlchemy compatibility issues")
        print("   Recommended: Use Python 3.11.9 for better compatibility")
        return False
    elif major == 3 and minor >= 11:
        print("✅ Python version is compatible")
        return True
    else:
        print("❌ Python version too old. Minimum required: 3.11")
        return False

def check_dependencies():
    """Check if dependencies are compatible"""
    try:
        import sqlalchemy
        print(f"SQLAlchemy version: {sqlalchemy.__version__}")
        
        # Check if we can import without errors
        from sqlalchemy.sql.elements import SQLCoreOperations
        print("✅ SQLAlchemy imports successfully")
        return True
    except ImportError as e:
        print(f"❌ SQLAlchemy import error: {e}")
        return False
    except Exception as e:
        print(f"❌ SQLAlchemy compatibility error: {e}")
        return False

def fix_gunicorn_command():
    """Update gunicorn command for better Render compatibility"""
    procfile_content = "web: gunicorn --bind 0.0.0.0:$PORT --workers 1 --timeout 60 main:app\n"
    
    with open("Procfile", "w") as f:
        f.write(procfile_content)
    
    print("✅ Updated Procfile with optimized gunicorn settings")

def create_render_requirements():
    """Create requirements.txt specifically for Render"""
    requirements = [
        "email-validator==2.1.0.post1",
        "Flask==3.0.3", 
        "Flask-Login==0.6.3",
        "Flask-SQLAlchemy==3.1.1",
        "gunicorn==22.0.0",
        "oauthlib==3.2.2",
        "psycopg2-binary==2.9.9",
        "PyJWT==2.8.0",
        "python-dotenv==1.0.1",
        "requests==2.32.3",
        "SQLAlchemy==2.0.32",
        "Werkzeug==3.0.3",
        "urllib3==2.2.2"
    ]
    
    with open("requirements.txt", "w") as f:
        f.write("\n".join(requirements) + "\n")
    
    print("✅ Created requirements.txt with compatible versions")

def update_runtime():
    """Set Python runtime for Render"""
    with open("runtime.txt", "w") as f:
        f.write("python-3.11.9\n")
    
    print("✅ Set Python runtime to 3.11.9")

def main():
    print("🔧 Fixing Render deployment issues...")
    print("=" * 50)
    
    # Check current environment
    check_python_version()
    
    # Fix deployment files
    create_render_requirements()
    update_runtime()
    fix_gunicorn_command()
    
    print("\n" + "=" * 50)
    print("✅ Render deployment fixes applied!")
    print("\n📋 Next steps:")
    print("1. Commit and push these changes to your GitHub repository")
    print("2. In Render dashboard, trigger a new deployment")
    print("3. Ensure environment variables are set correctly")
    print("4. Check deployment logs for any remaining issues")

if __name__ == "__main__":
    main()