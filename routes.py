from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User, AccessKey, AccessLog, PineScript, UserAccess
from tradingview import TradingViewAPI
import logging

main_bp = Blueprint('main', __name__)

# Home page - Key Entry or Login
@main_bp.route('/')
def index():
    return render_template('index.html')

# Key validation and user registration
@main_bp.route('/validate-key', methods=['POST'])
def validate_key():
    key_code = request.form.get('key_code', '').strip().upper()
    
    if not key_code:
        flash('Please enter an access key', 'error')
        return redirect(url_for('main.index'))
    
    # Remove any dashes or spaces from the key for comparison
    clean_key = key_code.replace('-', '').replace(' ', '')
    
    # Check if key exists and is active (try both clean and original key)
    access_key = AccessKey.query.filter_by(key_code=clean_key, status='active').first()
    if not access_key:
        access_key = AccessKey.query.filter_by(key_code=key_code, status='active').first()
    
    if not access_key:
        # Debug: Show available keys for troubleshooting
        logging.debug(f"Key lookup failed for: '{clean_key}' and '{key_code}'")
        all_keys = AccessKey.query.filter_by(status='active').all()
        logging.debug(f"Available active keys: {[key.key_code for key in all_keys]}")
        flash('Invalid or expired access key', 'error')
        return redirect(url_for('main.index'))
    
    # Store key info in session for registration
    session['pending_key'] = {
        'id': access_key.id,
        'key_code': access_key.key_code,
        'user_name': access_key.user_name,
        'user_email': access_key.user_email
    }
    
    return render_template('register.html', 
                         user_name=access_key.user_name, 
                         user_email=access_key.user_email)

# User registration with key
@main_bp.route('/register', methods=['POST'])
def register():
    if 'pending_key' not in session:
        flash('Invalid session. Please enter your access key again.', 'error')
        return redirect(url_for('main.index'))
    
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    
    if not email or not password:
        flash('Email and password are required', 'error')
        return render_template('register.html')
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('An account with this email already exists. Please login instead.', 'error')
        return redirect(url_for('main.manage_login'))
    
    # Get the pending key
    pending_key = session['pending_key']
    access_key = AccessKey.query.get(pending_key['id'])
    
    if not access_key or access_key.status != 'active':
        flash('Access key is no longer valid', 'error')
        return redirect(url_for('main.index'))
    
    # Create new user
    user = User(
        email=email,
        name=pending_key['user_name'],
        access_key_id=access_key.id
    )
    user.set_password(password)
    
    # Mark key as used
    access_key.mark_as_used()
    
    db.session.add(user)
    db.session.commit()
    
    # Login the user
    login_user(user)
    
    # Clear session
    session.pop('pending_key', None)
    
    flash('Account created successfully! Welcome to TradingView Access Manager.', 'success')
    return redirect(url_for('main.manage'))

# User login page (separate from admin)
@main_bp.route('/login', methods=['GET', 'POST'])
def manage_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('login.html')
        
        # Find user by email (only non-admin users)
        user = User.query.filter_by(email=email, is_admin=False).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.manage'))
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

# Admin login page (simplified with access code)
@main_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        access_code = request.form.get('access_code', '').strip()
        
        if not access_code:
            flash('Access code is required', 'error')
            return render_template('admin_login.html')
        
        # Check if access code is correct
        if access_code == 'ACCESS123':
            # Find admin user
            admin_user = User.query.filter_by(is_admin=True).first()
            if admin_user:
                login_user(admin_user)
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('main.admin'))
            else:
                flash('Admin user not found. Please contact system administrator.', 'error')
        else:
            flash('Invalid access code', 'error')
    
    return render_template('admin_login.html')

# Keep original login route for backwards compatibility  
@main_bp.route('/old-login', methods=['GET', 'POST'])
def login():
    return redirect(url_for('main.manage_login'))

# Logout
@main_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))

# Main management panel (was /manage, now main page for users)
@main_bp.route('/manage')
@login_required
def manage():
    if current_user.is_admin:
        flash('Admin users should use the admin panel. Redirecting...', 'info')
        return redirect(url_for('main.admin'))
    
    return render_template('manage.html')

# Admin panel (was dashboard, now /admin)
@main_bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('main.admin_login'))
    
    # Get all access keys with their associated users
    access_keys = AccessKey.query.order_by(AccessKey.created_at.desc()).all()
    
    # Get user access data for each key
    key_data = []
    for key in access_keys:
        key_info = {
            'key': key,
            'user': key.user,
            'accesses': []
        }
        
        if key.user:
            accesses = UserAccess.query.filter_by(user_id=key.user.id).all()
            for access in accesses:
                key_info['accesses'].append({
                    'pine_script': access.pine_script,
                    'tradingview_username': access.tradingview_username,
                    'granted_at': access.granted_at
                })
        
        key_data.append(key_info)
    
    # Get all Pine Scripts for management
    pine_scripts = PineScript.query.order_by(PineScript.name).all()
    
    return render_template('admin.html', key_data=key_data, pine_scripts=pine_scripts)

# Create new access key (admin only)
@main_bp.route('/admin/create-key', methods=['POST'])
@login_required
def create_key():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    data = request.get_json()
    user_name = data.get('user_name', '').strip()
    user_email = data.get('user_email', '').strip()
    
    if not user_name or not user_email:
        return jsonify({'success': False, 'message': 'Name and email are required'})
    
    # Generate unique key
    while True:
        key_code = AccessKey.generate_key()
        if not AccessKey.query.filter_by(key_code=key_code).first():
            break
    
    access_key = AccessKey(
        key_code=key_code,
        user_name=user_name,
        user_email=user_email
    )
    
    db.session.add(access_key)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Access key created successfully',
        'key_code': key_code
    })

# Remove user access from admin panel
@main_bp.route('/admin/remove-access', methods=['POST'])
@login_required
def admin_remove_access():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    data = request.get_json()
    user_id = data.get('user_id')
    pine_script_ids = data.get('pine_script_ids', [])
    
    if not user_id:
        return jsonify({'success': False, 'message': 'User ID is required'})
    
    user = User.query.get(user_id)
    if not user or not user.tradingview_username:
        return jsonify({'success': False, 'message': 'User not found or no TradingView username set'})
    
    try:
        tv_api = TradingViewAPI()
        
        # If specific scripts provided, remove only those; otherwise remove all
        if pine_script_ids:
            scripts_to_remove = PineScript.query.filter(PineScript.id.in_(pine_script_ids)).all()
        else:
            # Remove all access for this user
            user_accesses = UserAccess.query.filter_by(user_id=user_id).all()
            scripts_to_remove = [access.pine_script for access in user_accesses]
        
        # Remove access from all scripts at once
        pine_ids_to_remove = [script.pine_id for script in scripts_to_remove]
        results = tv_api.remove_access(user.tradingview_username, pine_ids_to_remove)
        
        removed_scripts = []
        for result in results:
            if result.get('removed', False):
                # Find corresponding script
                script = next((s for s in scripts_to_remove if s.pine_id == result['pine_id']), None)
                if script:
                    # Remove from database
                    UserAccess.query.filter_by(
                        user_id=user_id, 
                        pine_script_id=script.id
                    ).delete()
                    removed_scripts.append(script.name)
                    
                    # Log the action
                    log_entry = AccessLog(
                        user_id=current_user.id,
                        username=user.tradingview_username,
                        action='remove',
                        pine_script_id=script.pine_id,
                        status='success',
                        details=f'Removed by admin: {current_user.email}'
                    )
                    db.session.add(log_entry)
        
        # Reset user's access generation flag if all access removed
        remaining_access = UserAccess.query.filter_by(user_id=user_id).count()
        if remaining_access == 0:
            user.has_generated_access = False
            user.tradingview_username = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully removed access for {len(removed_scripts)} script(s)',
            'removed_scripts': removed_scripts
        })
    
    except Exception as e:
        logging.error(f"Error removing access: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

# API Routes for the management panel
@main_bp.route('/api/validate-username', methods=['POST'])
@login_required
def api_validate_username():
    logging.info(f"Username validation request received from user: {current_user.email}")
    
    if current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin accounts cannot manage TradingView access'})
    
    try:
        data = request.get_json()
        logging.info(f"Request data: {data}")
        
        if not data:
            logging.error("No JSON data received in request")
            return jsonify({'success': False, 'message': 'No data received'})
            
        username = data.get('username', '').strip()
        logging.info(f"Username to validate: '{username}'")
        
        if not username:
            logging.error("Empty username provided")
            return jsonify({'success': False, 'message': 'Username is required'})
        
        # Check if user already has access and username is different
        if current_user.has_generated_access and current_user.tradingview_username != username:
            logging.warning(f"User already has access for different username: {current_user.tradingview_username}")
            return jsonify({
                'success': False, 
                'message': f'You already have access granted for "{current_user.tradingview_username}". Please remove all access before switching users.'
            })
        
        # Initialize TradingView API
        try:
            tv_api = TradingViewAPI()
            logging.info("TradingView API initialized successfully")
            
            # Test authentication first
            if not tv_api._ensure_authenticated():
                logging.error("TradingView authentication failed")
                return jsonify({
                    'success': False, 
                    'message': 'TradingView authentication failed. Please contact administrator.'
                })
            
            logging.info("TradingView authentication verified")
            
        except Exception as api_init_error:
            logging.error(f"Failed to initialize TradingView API: {str(api_init_error)}")
            return jsonify({
                'success': False, 
                'message': f'TradingView API initialization failed. Please contact administrator.'
            })
        
        # Validate username
        logging.info(f"Calling TradingView API to validate username: {username}")
        result = tv_api.validate_username(username)
        logging.info(f"TradingView API validation result: {result}")
        
        if result.get('validuser', False):
            verified_username = result.get('verifiedUserName', username)
            logging.info(f"Username validation successful: {verified_username}")
            return jsonify({
                'success': True,
                'message': f'Username "{verified_username}" is valid',
                'data': {
                    'validuser': True,
                    'verifiedUserName': verified_username
                }
            })
        else:
            logging.warning(f"Username validation failed for: {username}")
            return jsonify({
                'success': False,
                'message': f'Username "{username}" not found on TradingView. Please check the spelling and try again.'
            })
    
    except Exception as e:
        logging.error(f"Username validation error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False, 
            'message': f'Server error during validation. Please try again or contact administrator.'
        })

@main_bp.route('/api/pine-scripts')
@login_required
def api_pine_scripts():
    scripts = PineScript.query.filter_by(active=True).all()
    return jsonify({
        'success': True,
        'scripts': [{
            'id': script.id,
            'pine_id': script.pine_id,
            'name': script.name,
            'description': script.description
        } for script in scripts]
    })

@main_bp.route('/api/grant-access', methods=['POST'])
@login_required
def api_grant_access():
    if current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin accounts cannot manage TradingView access'})
    
    data = request.get_json()
    username = data.get('username', '').strip()
    pine_ids = data.get('pine_script_ids', data.get('pine_ids', []))
    
    if not username or not pine_ids:
        return jsonify({'success': False, 'message': 'Username and pine script IDs are required'})
    
    # Check if user can generate access
    if current_user.has_generated_access and current_user.tradingview_username != username:
        return jsonify({
            'success': False,
            'message': 'You already have access for another username. Remove all access first.'
        })
    
    try:
        tv_api = TradingViewAPI()
        scripts = PineScript.query.filter(PineScript.pine_id.in_(pine_ids)).all()
        
        logging.info(f"Attempting to grant access for {username} to {len(pine_ids)} scripts: {pine_ids}")
        
        # Grant access to all scripts at once
        results = tv_api.grant_access(username, pine_ids)
        
        logging.info(f"TradingView API results: {results}")
        
        granted_count = 0
        failed_scripts = []
        
        for result in results:
            pine_id = result.get('pine_id')
            script = next((s for s in scripts if s.pine_id == pine_id), None)
            
            if script:
                if result.get('hasAccess', False) or result.get('status') == 'Success':
                    # Check if access already exists
                    existing_access = UserAccess.query.filter_by(
                        user_id=current_user.id,
                        pine_script_id=script.id
                    ).first()
                    
                    if not existing_access:
                        user_access = UserAccess(
                            user_id=current_user.id,
                            pine_script_id=script.id,
                            tradingview_username=username
                        )
                        db.session.add(user_access)
                        logging.info(f"Added access record for script {script.name}")
                    
                    # Log the action
                    log_entry = AccessLog(
                        user_id=current_user.id,
                        username=username,
                        action='grant',
                        pine_script_id=script.pine_id,
                        status='success',
                        details=f"API Response: {result.get('status', 'Unknown')}"
                    )
                    db.session.add(log_entry)
                    granted_count += 1
                else:
                    failed_scripts.append(script.name)
                    # Log failure
                    log_entry = AccessLog(
                        user_id=current_user.id,
                        username=username,
                        action='grant',
                        pine_script_id=script.pine_id,
                        status='failed',
                        details=f"API Response: {result.get('status', 'Failed')}"
                    )
                    db.session.add(log_entry)
                    logging.warning(f"Failed to grant access to {script.name}: {result}")
        
        # Update user flags if any access was granted
        if granted_count > 0:
            current_user.has_generated_access = True
            current_user.tradingview_username = username
        
        db.session.commit()
        
        if granted_count > 0:
            message = f'Successfully granted access to {granted_count} Pine Script(s) for {username}'
            if failed_scripts:
                message += f'. Failed: {", ".join(failed_scripts)}'
            
            return jsonify({
                'success': True,
                'message': message,
                'granted_count': granted_count,
                'failed_scripts': failed_scripts
            })
        else:
            return jsonify({
                'success': False,
                'message': f'Failed to grant access to any scripts. {", ".join(failed_scripts) if failed_scripts else ""}',
                'granted_count': 0,
                'failed_scripts': failed_scripts
            })
    
    except Exception as e:
        logging.error(f"Error granting access: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Server error: {str(e)}'
        })


# Admin Pine Script Management Routes
@main_bp.route('/admin/add-pine-script', methods=['POST'])
@login_required
def admin_add_pine_script():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    data = request.get_json()
    name = data.get('name', '').strip()
    pine_id = data.get('pine_id', '').strip()
    description = data.get('description', '').strip()
    
    if not name or not pine_id:
        return jsonify({'success': False, 'message': 'Name and Pine ID are required'})
    
    # Check if Pine Script with this ID already exists
    existing_script = PineScript.query.filter_by(pine_id=pine_id).first()
    if existing_script:
        return jsonify({'success': False, 'message': 'Pine Script with this ID already exists'})
    
    try:
        new_script = PineScript(
            name=name,
            pine_id=pine_id,
            description=description,
            active=True
        )
        db.session.add(new_script)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Pine Script "{name}" added successfully',
            'script': {
                'id': new_script.id,
                'name': new_script.name,
                'pine_id': new_script.pine_id,
                'description': new_script.description,
                'active': new_script.active,
                'created_at': new_script.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error adding Pine Script: {str(e)}")
        return jsonify({'success': False, 'message': f'Error adding Pine Script: {str(e)}'})


@main_bp.route('/admin/delete-pine-script/<int:script_id>', methods=['DELETE'])
@login_required
def admin_delete_pine_script(script_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    script = PineScript.query.get(script_id)
    if not script:
        return jsonify({'success': False, 'message': 'Pine Script not found'})
    
    try:
        # Check if any users have access to this script
        user_accesses = UserAccess.query.filter_by(pine_script_id=script_id).all()
        
        if user_accesses:
            # Remove all user accesses first
            for access in user_accesses:
                db.session.delete(access)
            
            # Log the removal
            for access in user_accesses:
                log_entry = AccessLog(
                    user_id=current_user.id,
                    username=access.tradingview_username,
                    action='remove',
                    pine_script_id=script.pine_id,
                    status='success',
                    details=f'Script deleted by admin: {current_user.email}'
                )
                db.session.add(log_entry)
        
        # Delete the script
        db.session.delete(script)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Pine Script "{script.name}" deleted successfully',
            'removed_accesses': len(user_accesses)
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting Pine Script: {str(e)}")
        return jsonify({'success': False, 'message': f'Error deleting Pine Script: {str(e)}'})


@main_bp.route('/admin/toggle-pine-script/<int:script_id>', methods=['POST'])
@login_required
def admin_toggle_pine_script(script_id):
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    script = PineScript.query.get(script_id)
    if not script:
        return jsonify({'success': False, 'message': 'Pine Script not found'})
    
    try:
        script.active = not script.active
        db.session.commit()
        
        status = 'activated' if script.active else 'deactivated'
        return jsonify({
            'success': True,
            'message': f'Pine Script "{script.name}" {status} successfully',
            'active': script.active
        })
    
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error toggling Pine Script: {str(e)}")
        return jsonify({'success': False, 'message': f'Error toggling Pine Script: {str(e)}'})


@main_bp.route('/admin/pine-scripts', methods=['GET'])
@login_required
def admin_get_pine_scripts():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    scripts = PineScript.query.order_by(PineScript.name).all()
    return jsonify({
        'success': True,
        'scripts': [{
            'id': script.id,
            'name': script.name,
            'pine_id': script.pine_id,
            'description': script.description,
            'active': script.active,
            'created_at': script.created_at.strftime('%Y-%m-%d %H:%M'),
            'user_count': UserAccess.query.filter_by(pine_script_id=script.id).count()
        } for script in scripts]
    })


# Admin Data Management Routes
@main_bp.route('/admin/backup', methods=['POST'])
@login_required
def admin_create_backup():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from backup_system import BackupManager
        backup_manager = BackupManager()
        
        data = request.get_json() or {}
        backup_name = data.get('name')
        
        backup_file = backup_manager.create_backup(backup_name)
        if backup_file:
            return jsonify({
                'success': True,
                'message': 'Backup created successfully',
                'backup_file': os.path.basename(backup_file)
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to create backup'
            })
    
    except Exception as e:
        logging.error(f"Error creating backup: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error creating backup: {str(e)}'
        })


@main_bp.route('/admin/backups', methods=['GET'])
@login_required
def admin_list_backups():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from backup_system import BackupManager
        backup_manager = BackupManager()
        
        backups = backup_manager.list_backups()
        backup_data = []
        
        for backup in backups:
            backup_data.append({
                'name': backup['name'],
                'size': backup['size'],
                'size_mb': round(backup['size'] / (1024 * 1024), 2),
                'modified': backup['modified'].strftime('%Y-%m-%d %H:%M:%S')
            })
        
        return jsonify({
            'success': True,
            'backups': backup_data
        })
    
    except Exception as e:
        logging.error(f"Error listing backups: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error listing backups: {str(e)}'
        })


@main_bp.route('/admin/health-check', methods=['GET'])
@login_required
def admin_health_check():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from data_recovery import DataRecovery
        recovery = DataRecovery()
        
        health = recovery.check_database_health()
        return jsonify({
            'success': True,
            'health': health
        })
    
    except Exception as e:
        logging.error(f"Error checking health: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error checking health: {str(e)}'
        })


@main_bp.route('/admin/validate-data', methods=['POST'])
@login_required
def admin_validate_data():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from data_recovery import DataRecovery
        recovery = DataRecovery()
        
        result = recovery.validate_data_integrity()
        return jsonify({
            'success': True,
            'validation_result': result
        })
    
    except Exception as e:
        logging.error(f"Error validating data: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error validating data: {str(e)}'
        })


@main_bp.route('/admin/recover-defaults', methods=['POST'])
@login_required
def admin_recover_defaults():
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin access required'}), 403
    
    try:
        from data_recovery import DataRecovery
        recovery = DataRecovery()
        
        result = recovery.recover_default_data()
        return jsonify({
            'success': True,
            'recovery_result': result
        })
    
    except Exception as e:
        logging.error(f"Error recovering defaults: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Error recovering defaults: {str(e)}'
        })

@main_bp.route('/api/remove-access', methods=['POST'])
@login_required
def api_remove_access():
    if current_user.is_admin:
        return jsonify({'success': False, 'message': 'Admin accounts cannot manage TradingView access'})
    
    data = request.get_json()
    username = data.get('username', current_user.tradingview_username)
    
    if not username:
        return jsonify({'success': False, 'message': 'No username to remove access for'})
    
    try:
        tv_api = TradingViewAPI()
        
        # Get all user accesses
        user_accesses = UserAccess.query.filter_by(user_id=current_user.id).all()
        pine_ids_to_remove = [access.pine_script.pine_id for access in user_accesses]
        
        # Remove access from all scripts at once
        results = tv_api.remove_access(username, pine_ids_to_remove)
        
        removed_count = 0
        for result in results:
            if result.get('removed', False):
                # Find and remove the corresponding access
                access = next((a for a in user_accesses if a.pine_script.pine_id == result['pine_id']), None)
                if access:
                    db.session.delete(access)
                    
                    # Log the action
                    log_entry = AccessLog(
                        user_id=current_user.id,
                        username=username,
                        action='remove',
                        pine_script_id=access.pine_script.pine_id,
                        status='success'
                    )
                    db.session.add(log_entry)
                    removed_count += 1
        
        # Reset user flags
        current_user.has_generated_access = False
        current_user.tradingview_username = None
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Successfully removed all access for {username}'
        })
    
    except Exception as e:
        logging.error(f"Remove access error: {str(e)}")
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})