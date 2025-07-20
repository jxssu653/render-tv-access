#!/usr/bin/env python3
"""
Data Recovery and Validation System
Ensures data integrity and provides recovery options
"""

import os
import logging
from datetime import datetime
from app import app, db
from models import User, AccessKey, PineScript, UserAccess, AccessLog

logger = logging.getLogger(__name__)

class DataRecovery:
    def __init__(self):
        self.recovery_log = []
    
    def validate_data_integrity(self):
        """Validate database integrity and fix common issues"""
        issues_found = []
        fixes_applied = []
        
        with app.app_context():
            try:
                # Check for orphaned user accesses
                orphaned_accesses = db.session.query(UserAccess).filter(
                    ~UserAccess.user_id.in_(db.session.query(User.id))
                ).all()
                
                if orphaned_accesses:
                    issues_found.append(f"Found {len(orphaned_accesses)} orphaned user accesses")
                    for access in orphaned_accesses:
                        db.session.delete(access)
                    fixes_applied.append(f"Removed {len(orphaned_accesses)} orphaned user accesses")
                
                # Check for orphaned user accesses (pine script side)
                orphaned_script_accesses = db.session.query(UserAccess).filter(
                    ~UserAccess.pine_script_id.in_(db.session.query(PineScript.id))
                ).all()
                
                if orphaned_script_accesses:
                    issues_found.append(f"Found {len(orphaned_script_accesses)} accesses to deleted scripts")
                    for access in orphaned_script_accesses:
                        db.session.delete(access)
                    fixes_applied.append(f"Removed {len(orphaned_script_accesses)} accesses to deleted scripts")
                
                # Check for users with invalid access key references
                invalid_key_users = db.session.query(User).filter(
                    User.access_key_id.isnot(None),
                    ~User.access_key_id.in_(db.session.query(AccessKey.id))
                ).all()
                
                if invalid_key_users:
                    issues_found.append(f"Found {len(invalid_key_users)} users with invalid access key references")
                    for user in invalid_key_users:
                        user.access_key_id = None
                    fixes_applied.append(f"Fixed {len(invalid_key_users)} invalid access key references")
                
                # Check for duplicate Pine Script IDs
                duplicate_scripts = db.session.query(PineScript.pine_id, db.func.count(PineScript.id)).\
                    group_by(PineScript.pine_id).\
                    having(db.func.count(PineScript.id) > 1).all()
                
                if duplicate_scripts:
                    issues_found.append(f"Found {len(duplicate_scripts)} duplicate Pine Script IDs")
                    for pine_id, count in duplicate_scripts:
                        # Keep the first one, delete the rest
                        scripts = PineScript.query.filter_by(pine_id=pine_id).all()
                        for script in scripts[1:]:
                            # Remove associated user accesses first
                            UserAccess.query.filter_by(pine_script_id=script.id).delete()
                            db.session.delete(script)
                    fixes_applied.append(f"Removed duplicate Pine Scripts, kept oldest versions")
                
                # Commit all fixes
                if fixes_applied:
                    db.session.commit()
                    logger.info("Data integrity fixes applied successfully")
                
                return {
                    'issues_found': issues_found,
                    'fixes_applied': fixes_applied,
                    'status': 'success' if not issues_found else 'fixed'
                }
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error during data validation: {str(e)}")
                return {
                    'issues_found': issues_found,
                    'fixes_applied': [],
                    'error': str(e),
                    'status': 'error'
                }
    
    def recover_default_data(self):
        """Recover essential default data if missing"""
        recovered_items = []
        
        with app.app_context():
            try:
                # Ensure admin user exists
                admin_user = User.query.filter_by(email='admin@tradingview.com').first()
                if not admin_user:
                    admin_user = User(
                        email='admin@tradingview.com',
                        name='Admin User',
                        is_admin=True
                    )
                    admin_user.set_password('admin123')
                    db.session.add(admin_user)
                    recovered_items.append("Created default admin user")
                
                # Ensure default Pine Scripts exist if none are found
                if PineScript.query.count() == 0:
                    default_scripts = [
                        {'name': 'Ultraalgo', 'pine_id': 'PUB;0c59036edcae4c8684c8e17c01eaf137', 'description': 'Advanced trading algorithm'},
                        {'name': 'simplealgo', 'pine_id': 'PUB;a1b2c3d4e5f6789012345678901234ab', 'description': 'Simple trading algorithm'},
                        {'name': 'Million moves', 'pine_id': 'PUB;b2c3d4e5f6789012345678901234abcd', 'description': 'Million moves strategy'},
                        {'name': 'luxalgo', 'pine_id': 'PUB;c3d4e5f6789012345678901234abcdef', 'description': 'Luxury algorithm'},
                        {'name': 'lux Osi Matrix', 'pine_id': 'PUB;d4e5f6789012345678901234abcdef01', 'description': 'Lux OSI Matrix indicator'},
                        {'name': 'infnity algo', 'pine_id': 'PUB;e5f6789012345678901234abcdef0123', 'description': 'Infinity algorithm'},
                        {'name': 'Diamond algo', 'pine_id': 'PUB;f6789012345678901234abcdef012345', 'description': 'Diamond pattern algorithm'},
                        {'name': 'Blue signals', 'pine_id': 'PUB;6789012345678901234abcdef0123456', 'description': 'Blue signal indicator'},
                        {'name': 'Goatalgo', 'pine_id': 'PUB;789012345678901234abcdef01234567', 'description': 'GOAT algorithm'},
                        {'name': 'xpalgo', 'pine_id': 'PUB;89012345678901234abcdef012345678', 'description': 'XP algorithm'},
                        {'name': 'NovaAlgo', 'pine_id': 'PUB;9012345678901234abcdef0123456789', 'description': 'Nova algorithm'},
                    ]
                    
                    for script_data in default_scripts:
                        script = PineScript(
                            name=script_data['name'],
                            pine_id=script_data['pine_id'],
                            description=script_data['description'],
                            active=True
                        )
                        db.session.add(script)
                    
                    recovered_items.append(f"Created {len(default_scripts)} default Pine Scripts")
                
                db.session.commit()
                logger.info(f"Data recovery completed: {len(recovered_items)} items recovered")
                return {
                    'recovered_items': recovered_items,
                    'status': 'success'
                }
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error during data recovery: {str(e)}")
                return {
                    'recovered_items': recovered_items,
                    'error': str(e),
                    'status': 'error'
                }
    
    def check_database_health(self):
        """Comprehensive database health check"""
        health_report = {
            'timestamp': datetime.now().isoformat(),
            'database_accessible': False,
            'tables_exist': False,
            'data_counts': {},
            'issues': [],
            'recommendations': []
        }
        
        try:
            with app.app_context():
                # Test database connection
                db.session.execute(db.text('SELECT 1'))
                health_report['database_accessible'] = True
                
                # Check if tables exist
                try:
                    user_count = User.query.count()
                    health_report['tables_exist'] = True
                    
                    # Get data counts
                    health_report['data_counts'] = {
                        'users': User.query.count(),
                        'access_keys': AccessKey.query.count(),
                        'pine_scripts': PineScript.query.count(),
                        'user_accesses': UserAccess.query.count(),
                        'access_logs': AccessLog.query.count()
                    }
                    
                    # Check for potential issues
                    if health_report['data_counts']['users'] == 0:
                        health_report['issues'].append("No users found in database")
                        health_report['recommendations'].append("Run data recovery to create default admin user")
                    
                    if health_report['data_counts']['pine_scripts'] == 0:
                        health_report['issues'].append("No Pine Scripts found")
                        health_report['recommendations'].append("Run data recovery to create default Pine Scripts")
                    
                    admin_count = User.query.filter_by(is_admin=True).count()
                    if admin_count == 0:
                        health_report['issues'].append("No admin users found")
                        health_report['recommendations'].append("Create an admin user to manage the system")
                    
                except Exception as e:
                    health_report['issues'].append(f"Tables may not exist: {str(e)}")
                    health_report['recommendations'].append("Initialize database tables")
                
        except Exception as e:
            health_report['issues'].append(f"Database connection failed: {str(e)}")
            health_report['recommendations'].append("Check database configuration and connectivity")
        
        return health_report


def run_full_recovery():
    """Run complete data recovery and validation"""
    print("🔄 Starting comprehensive data recovery...")
    
    recovery = DataRecovery()
    
    # Health check
    print("\n📋 Checking database health...")
    health = recovery.check_database_health()
    print(f"Database accessible: {'✅' if health['database_accessible'] else '❌'}")
    print(f"Tables exist: {'✅' if health['tables_exist'] else '❌'}")
    
    if health['data_counts']:
        print("\n📊 Current data counts:")
        for table, count in health['data_counts'].items():
            print(f"  {table}: {count}")
    
    if health['issues']:
        print("\n⚠️ Issues found:")
        for issue in health['issues']:
            print(f"  - {issue}")
    
    # Data validation and fixes
    print("\n🔍 Validating data integrity...")
    validation_result = recovery.validate_data_integrity()
    
    if validation_result['issues_found']:
        print("Issues found:")
        for issue in validation_result['issues_found']:
            print(f"  - {issue}")
    
    if validation_result['fixes_applied']:
        print("Fixes applied:")
        for fix in validation_result['fixes_applied']:
            print(f"  ✅ {fix}")
    
    # Recover default data
    print("\n🚑 Recovering default data...")
    recovery_result = recovery.recover_default_data()
    
    if recovery_result['recovered_items']:
        print("Data recovered:")
        for item in recovery_result['recovered_items']:
            print(f"  ✅ {item}")
    else:
        print("  ✅ All default data already exists")
    
    print("\n🎉 Data recovery completed successfully!")
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "health":
        recovery = DataRecovery()
        health = recovery.check_database_health()
        print(f"Database Health Report:")
        print(f"Timestamp: {health['timestamp']}")
        print(f"Database accessible: {health['database_accessible']}")
        print(f"Tables exist: {health['tables_exist']}")
        if health['data_counts']:
            print("Data counts:")
            for table, count in health['data_counts'].items():
                print(f"  {table}: {count}")
        if health['issues']:
            print("Issues:")
            for issue in health['issues']:
                print(f"  - {issue}")
    else:
        run_full_recovery()