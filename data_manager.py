#!/usr/bin/env python3
"""
Data Manager - Command line interface for database management
Provides backup, restore, and maintenance operations
"""

import os
import sys
import argparse
from datetime import datetime
from backup_system import BackupManager
from data_recovery import DataRecovery, run_full_recovery

def main():
    parser = argparse.ArgumentParser(description='TradingView Access Manager - Database Management')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Backup commands
    backup_parser = subparsers.add_parser('backup', help='Create database backup')
    backup_parser.add_argument('--name', help='Backup name (optional)')
    backup_parser.add_argument('--auto', action='store_true', help='Create automatic backup')
    
    # Restore commands
    restore_parser = subparsers.add_parser('restore', help='Restore from backup')
    restore_parser.add_argument('file', help='Backup file to restore from')
    
    # List commands
    list_parser = subparsers.add_parser('list', help='List available backups')
    
    # Health commands
    health_parser = subparsers.add_parser('health', help='Check database health')
    
    # Recovery commands
    recovery_parser = subparsers.add_parser('recover', help='Run data recovery')
    recovery_parser.add_argument('--validate', action='store_true', help='Validate data integrity')
    recovery_parser.add_argument('--defaults', action='store_true', help='Recover default data')
    recovery_parser.add_argument('--full', action='store_true', help='Run full recovery')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize managers
    backup_manager = BackupManager()
    recovery = DataRecovery()
    
    try:
        if args.command == 'backup':
            if args.auto:
                backup_file = backup_manager.auto_backup()
            else:
                backup_file = backup_manager.create_backup(args.name)
            
            if backup_file:
                print(f"✅ Backup created: {os.path.basename(backup_file)}")
            else:
                print("❌ Backup failed")
                sys.exit(1)
        
        elif args.command == 'restore':
            backup_file = args.file
            if not backup_file.endswith('.json'):
                backup_file = os.path.join(backup_manager.backup_dir, f"{backup_file}.json")
            
            if backup_manager.restore_backup(backup_file):
                print("✅ Restore completed successfully")
            else:
                print("❌ Restore failed")
                sys.exit(1)
        
        elif args.command == 'list':
            backups = backup_manager.list_backups()
            if not backups:
                print("No backups found")
            else:
                print(f"{'Name':<40} {'Size':<10} {'Date':<20}")
                print("-" * 70)
                for backup in backups:
                    size_mb = backup['size'] / (1024 * 1024)
                    date_str = backup['modified'].strftime('%Y-%m-%d %H:%M:%S')
                    print(f"{backup['name']:<40} {size_mb:.2f}MB{'':<3} {date_str}")
        
        elif args.command == 'health':
            health = recovery.check_database_health()
            print("Database Health Report")
            print("=" * 50)
            print(f"Timestamp: {health['timestamp']}")
            print(f"Database accessible: {'✅' if health['database_accessible'] else '❌'}")
            print(f"Tables exist: {'✅' if health['tables_exist'] else '❌'}")
            
            if health['data_counts']:
                print("\nData Counts:")
                for table, count in health['data_counts'].items():
                    print(f"  {table}: {count}")
            
            if health['issues']:
                print("\n⚠️ Issues Found:")
                for issue in health['issues']:
                    print(f"  - {issue}")
                
                print("\n💡 Recommendations:")
                for rec in health['recommendations']:
                    print(f"  - {rec}")
            else:
                print("\n✅ No issues found")
        
        elif args.command == 'recover':
            if args.full:
                run_full_recovery()
            elif args.validate:
                result = recovery.validate_data_integrity()
                if result['issues_found']:
                    print("Issues found and fixed:")
                    for fix in result['fixes_applied']:
                        print(f"  ✅ {fix}")
                else:
                    print("✅ No data integrity issues found")
            elif args.defaults:
                result = recovery.recover_default_data()
                if result['recovered_items']:
                    print("Default data recovered:")
                    for item in result['recovered_items']:
                        print(f"  ✅ {item}")
                else:
                    print("✅ All default data already exists")
            else:
                print("Please specify recovery type: --validate, --defaults, or --full")
                sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()