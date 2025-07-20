#!/usr/bin/env python3
"""
Database Backup and Restore System for TradingView Access Manager
Ensures data persistence and prevents data loss during restarts/deployments
"""

import os
import json
import logging
from datetime import datetime
from app import app, db
from models import User, AccessKey, PineScript, UserAccess, AccessLog

logger = logging.getLogger(__name__)

class BackupManager:
    def __init__(self):
        self.backup_dir = os.path.join(os.getcwd(), 'backups')
        self.ensure_backup_directory()
    
    def ensure_backup_directory(self):
        """Create backup directory if it doesn't exist"""
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logger.info(f"Created backup directory: {self.backup_dir}")
    
    def create_backup(self, backup_name=None):
        """Create a complete backup of all data"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_data = {
            'timestamp': datetime.now().isoformat(),
            'version': '1.0',
            'users': [],
            'access_keys': [],
            'pine_scripts': [],
            'user_accesses': [],
            'access_logs': []
        }
        
        try:
            with app.app_context():
                # Backup Users
                users = User.query.all()
                for user in users:
                    backup_data['users'].append({
                        'id': user.id,
                        'email': user.email,
                        'password_hash': user.password_hash,
                        'name': user.name,
                        'is_admin': user.is_admin,
                        'access_key_id': user.access_key_id,
                        'tradingview_username': user.tradingview_username,
                        'has_generated_access': user.has_generated_access,
                        'created_at': user.created_at.isoformat() if user.created_at else None,
                        'updated_at': user.updated_at.isoformat() if user.updated_at else None
                    })
                
                # Backup Access Keys
                access_keys = AccessKey.query.all()
                for key in access_keys:
                    backup_data['access_keys'].append({
                        'id': key.id,
                        'key_code': key.key_code,
                        'user_name': key.user_name,
                        'user_email': key.user_email,
                        'status': key.status,
                        'created_by_admin': key.created_by_admin,
                        'created_at': key.created_at.isoformat() if key.created_at else None,
                        'used_at': key.used_at.isoformat() if key.used_at else None
                    })
                
                # Backup Pine Scripts
                pine_scripts = PineScript.query.all()
                for script in pine_scripts:
                    backup_data['pine_scripts'].append({
                        'id': script.id,
                        'name': script.name,
                        'pine_id': script.pine_id,
                        'description': script.description,
                        'active': script.active,
                        'created_at': script.created_at.isoformat() if script.created_at else None
                    })
                
                # Backup User Accesses
                user_accesses = UserAccess.query.all()
                for access in user_accesses:
                    backup_data['user_accesses'].append({
                        'id': access.id,
                        'user_id': access.user_id,
                        'pine_script_id': access.pine_script_id,
                        'tradingview_username': access.tradingview_username,
                        'granted_at': access.granted_at.isoformat() if access.granted_at else None
                    })
                
                # Backup Access Logs
                access_logs = AccessLog.query.all()
                for log in access_logs:
                    backup_data['access_logs'].append({
                        'id': log.id,
                        'user_id': log.user_id,
                        'username': log.username,
                        'action': log.action,
                        'pine_script_id': log.pine_script_id,
                        'status': log.status,
                        'details': log.details,
                        'timestamp': log.timestamp.isoformat() if log.timestamp else None
                    })
            
            # Save backup file
            backup_file = os.path.join(self.backup_dir, f"{backup_name}.json")
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            logger.info(f"Backup created successfully: {backup_file}")
            print(f"✅ Database backup created: {backup_name}.json")
            return backup_file
            
        except Exception as e:
            logger.error(f"Error creating backup: {str(e)}")
            print(f"❌ Error creating backup: {str(e)}")
            return None
    
    def restore_backup(self, backup_file):
        """Restore data from backup file"""
        if not os.path.exists(backup_file):
            logger.error(f"Backup file not found: {backup_file}")
            return False
        
        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            
            with app.app_context():
                # Clear existing data (with confirmation)
                print("⚠️  WARNING: This will replace ALL existing data!")
                confirm = input("Type 'CONFIRM' to proceed with restore: ")
                if confirm != 'CONFIRM':
                    print("❌ Restore cancelled")
                    return False
                
                # Clear tables in reverse dependency order
                UserAccess.query.delete()
                AccessLog.query.delete()
                User.query.delete()
                AccessKey.query.delete()
                PineScript.query.delete()
                db.session.commit()
                
                # Restore Pine Scripts first (no dependencies)
                for script_data in backup_data.get('pine_scripts', []):
                    script = PineScript(
                        name=script_data['name'],
                        pine_id=script_data['pine_id'],
                        description=script_data.get('description'),
                        active=script_data.get('active', True)
                    )
                    if script_data.get('created_at'):
                        script.created_at = datetime.fromisoformat(script_data['created_at'])
                    db.session.add(script)
                
                # Restore Access Keys
                for key_data in backup_data.get('access_keys', []):
                    key = AccessKey(
                        key_code=key_data['key_code'],
                        user_name=key_data['user_name'],
                        user_email=key_data['user_email'],
                        status=key_data.get('status', 'active'),
                        created_by_admin=key_data.get('created_by_admin', True)
                    )
                    if key_data.get('created_at'):
                        key.created_at = datetime.fromisoformat(key_data['created_at'])
                    if key_data.get('used_at'):
                        key.used_at = datetime.fromisoformat(key_data['used_at'])
                    db.session.add(key)
                
                # Restore Users
                for user_data in backup_data.get('users', []):
                    user = User(
                        email=user_data['email'],
                        password_hash=user_data['password_hash'],
                        name=user_data['name'],
                        is_admin=user_data.get('is_admin', False),
                        access_key_id=user_data.get('access_key_id'),
                        tradingview_username=user_data.get('tradingview_username'),
                        has_generated_access=user_data.get('has_generated_access', False)
                    )
                    if user_data.get('created_at'):
                        user.created_at = datetime.fromisoformat(user_data['created_at'])
                    if user_data.get('updated_at'):
                        user.updated_at = datetime.fromisoformat(user_data['updated_at'])
                    db.session.add(user)
                
                db.session.commit()
                
                # Restore User Accesses
                for access_data in backup_data.get('user_accesses', []):
                    access = UserAccess(
                        user_id=access_data['user_id'],
                        pine_script_id=access_data['pine_script_id'],
                        tradingview_username=access_data['tradingview_username']
                    )
                    if access_data.get('granted_at'):
                        access.granted_at = datetime.fromisoformat(access_data['granted_at'])
                    db.session.add(access)
                
                # Restore Access Logs
                for log_data in backup_data.get('access_logs', []):
                    log = AccessLog(
                        user_id=log_data.get('user_id'),
                        username=log_data['username'],
                        action=log_data['action'],
                        pine_script_id=log_data.get('pine_script_id'),
                        status=log_data['status'],
                        details=log_data.get('details')
                    )
                    if log_data.get('timestamp'):
                        log.timestamp = datetime.fromisoformat(log_data['timestamp'])
                    db.session.add(log)
                
                db.session.commit()
            
            logger.info(f"Backup restored successfully from: {backup_file}")
            print(f"✅ Database restored from backup: {backup_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {str(e)}")
            print(f"❌ Error restoring backup: {str(e)}")
            return False
    
    def list_backups(self):
        """List all available backup files"""
        backup_files = []
        if os.path.exists(self.backup_dir):
            for file in os.listdir(self.backup_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(self.backup_dir, file)
                    stat = os.stat(file_path)
                    backup_files.append({
                        'name': file,
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime)
                    })
        
        backup_files.sort(key=lambda x: x['modified'], reverse=True)
        return backup_files
    
    def auto_backup(self):
        """Create automatic backup (called on app startup)"""
        try:
            backup_file = self.create_backup(f"auto_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            if backup_file:
                # Keep only last 10 auto backups
                self.cleanup_old_backups(keep_count=10, prefix="auto_backup_")
            return backup_file
        except Exception as e:
            logger.error(f"Auto backup failed: {str(e)}")
            return None
    
    def cleanup_old_backups(self, keep_count=10, prefix="auto_backup_"):
        """Remove old backup files, keeping only the specified count"""
        try:
            backup_files = [f for f in self.list_backups() if f['name'].startswith(prefix)]
            if len(backup_files) > keep_count:
                files_to_remove = backup_files[keep_count:]
                for file_info in files_to_remove:
                    os.remove(file_info['path'])
                    logger.info(f"Removed old backup: {file_info['name']}")
        except Exception as e:
            logger.error(f"Error cleaning up backups: {str(e)}")


def init_backup_system():
    """Initialize backup system and create initial backup if needed"""
    backup_manager = BackupManager()
    
    # Create automatic backup on startup
    logger.info("Creating automatic backup on startup...")
    backup_file = backup_manager.auto_backup()
    
    return backup_manager


if __name__ == "__main__":
    import sys
    
    backup_manager = BackupManager()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python backup_system.py backup [name]     - Create backup")
        print("  python backup_system.py restore <file>    - Restore from backup")
        print("  python backup_system.py list             - List backups")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "backup":
        name = sys.argv[2] if len(sys.argv) > 2 else None
        backup_manager.create_backup(name)
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Error: Please specify backup file")
            sys.exit(1)
        backup_file = sys.argv[2]
        if not backup_file.endswith('.json'):
            backup_file = os.path.join(backup_manager.backup_dir, f"{backup_file}.json")
        backup_manager.restore_backup(backup_file)
    
    elif command == "list":
        backups = backup_manager.list_backups()
        if not backups:
            print("No backups found")
        else:
            print("Available backups:")
            for backup in backups:
                size_mb = backup['size'] / (1024 * 1024)
                print(f"  {backup['name']} - {size_mb:.2f}MB - {backup['modified']}")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)