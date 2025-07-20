#!/usr/bin/env python3
"""
Script to add Pine Scripts to the database
"""
from app import app, db
from models import PineScript

def add_pine_scripts():
    """Add the Pine Scripts to the database"""
    
    pine_scripts = [
        {
            'pine_id': 'PUB;0c59036edcae4c8684c8e17c01eaf137',
            'name': 'Ultraalgo',
            'description': 'Advanced trading algorithm with ultra-fast signals'
        },
        {
            'pine_id': 'PUB;a3690bb3cb3549e7af0378a978f96a43',
            'name': 'simplealgo',
            'description': 'Simple and effective trading algorithm'
        },
        {
            'pine_id': 'PUB;53828990c8014de895162ec99f480803',
            'name': 'Million moves.',
            'description': 'High-frequency trading signals for maximum moves'
        },
        {
            'pine_id': 'PUB;b73e59a4d74e4d3d9a449ad1187b786b',
            'name': 'luxalgo',
            'description': 'Premium luxury trading algorithm'
        },
        {
            'pine_id': 'PUB;996c8fa1a3d74270b95e24643df04fd5',
            'name': 'lux Osi Matrix',
            'description': 'Advanced oscillator matrix for luxury trading'
        },
        {
            'pine_id': 'PUB;bfb44fdc5d234c4f8aa5fd06f1bf56a6',
            'name': 'infnity algo',
            'description': 'Infinite possibilities trading algorithm'
        },
        {
            'pine_id': 'PUB;504fed266bcf48d8ad1d2c7bbe1927ff',
            'name': 'Diamond algo',
            'description': 'Premium diamond-grade trading signals'
        },
        {
            'pine_id': 'PUB;278e02e275914ad5a5cec9ce0e9d9d22',
            'name': 'Blue signals',
            'description': 'Clear blue trading signals for all markets'
        },
        {
            'pine_id': 'PUB;0a056b6e1feb4183abf6e601d4140189',
            'name': 'Goatalgo',
            'description': 'Greatest of all time trading algorithm'
        },
        {
            'pine_id': 'PUB;5e901ec6f78043b4bca09e8c2f911e01',
            'name': 'xpalgo',
            'description': 'Experience-powered trading algorithm'
        },
        {
            'pine_id': 'PUB;f42a2d8c9ede4bc4b005fb8e56b500cc',
            'name': 'NovaAlgo',
            'description': 'New star trading algorithm with explosive signals'
        }
    ]
    
    with app.app_context():
        added_count = 0
        updated_count = 0
        
        for script_data in pine_scripts:
            # Check if script already exists
            existing_script = PineScript.query.filter_by(pine_id=script_data['pine_id']).first()
            
            if existing_script:
                # Update existing script
                existing_script.name = script_data['name']
                existing_script.description = script_data['description']
                existing_script.active = True
                updated_count += 1
                print(f"✅ Updated: {script_data['name']}")
            else:
                # Add new script
                new_script = PineScript(
                    pine_id=script_data['pine_id'],
                    name=script_data['name'],
                    description=script_data['description'],
                    active=True
                )
                db.session.add(new_script)
                added_count += 1
                print(f"➕ Added: {script_data['name']}")
        
        db.session.commit()
        
        print(f"\n📊 Summary:")
        print(f"   Added: {added_count} new Pine Scripts")
        print(f"   Updated: {updated_count} existing Pine Scripts")
        print(f"   Total: {len(pine_scripts)} Pine Scripts in database")

if __name__ == "__main__":
    add_pine_scripts()