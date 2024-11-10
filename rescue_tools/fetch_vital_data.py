"""
Firebase Real-time Database Manager for Rescue Operations
======================================================

This module handles real-time database operations for disaster rescue operations using Firebase.
It manages victim data, rescue statuses, and emergency priorities in real-time.

Key Features:
    - Real-time database initialization
    - Unique key generation for victims
    - Status and time updates
    - JSON template management
    - Error handling for database operations

Dependencies:
    - firebase_admin: For Firebase operations
    - json: For JSON data handling
    - datetime: For timestamp management
    - os: For file operations

Configuration:
    Requires a Firebase admin SDK JSON credential file and valid database URL.
"""

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
import os
import datetime

# Get current timestamp
time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Initialize Firebase with credentials
cred = credentials.Certificate("rescue_tools/disasterrescueai-firebase-adminsdk.json")

try:
    firebase_admin.initialize_app(
        credential=cred,
        options={'databaseURL': 'https://disasterrescueai-default-rtdb.firebaseio.com'},
        name='RescueTeam_RealTimeDatabase'
    )
except:
    pass  # App already initialized

# Get database instance
db = firebase_admin.db

def set_key(json_data: dict) -> str:
    """
    Creates a new entry in the Firebase database with a unique key.
    
    Args:
        json_data (dict): Victim data to be stored in the database
        
    Returns:
        str: Unique identifier (key) for the created database entry
        
    Example:
        >>> victim_data = {"name": "John Doe", "status": "pending"}
        >>> victim_id = set_key(victim_data)
        >>> print(victim_id)
        '-NcX4tY2ZpKvgDX7j8Q9'
        
    Notes:
        - Automatically generates a unique Firebase key
        - Creates a new child node in 'rescue_team_dataset'
        - Returns the generated key for future reference
    """
    ref = db.reference('rescue_team_dataset', 
                      app=firebase_admin.get_app(name='RescueTeam_RealTimeDatabase'))
    # Generate a unique key
    new_key = ref.push().key
    # Add the data with the unique key
    ref.child(new_key).set(json_data)
    return new_key

def update_time_and_status(ref: db.Reference, 
                          victim_id: str, 
                          time: str, 
                          rescue_status: str, 
                          emergency_status: str) -> None:
    """
    Updates timestamp and status information for a specific victim.
    
    Args:
        ref (db.Reference): Firebase database reference
        victim_id (str): Unique identifier for the victim
        time (str): Current timestamp
        rescue_status (str): Current rescue status (e.g., 'pending', 'in_progress')
        emergency_status (str): Priority level of the emergency
        
    Notes:
        - Updates three fields: last_updated, rescue_status, and emergency_status
        - Uses atomic update operation for data consistency
    """
    ref.child(victim_id).update({
        'last_updated': time,
        'rescue_status': rescue_status,
        'emergency_status': emergency_status
    })

def update_(victim_id: str, json_data: dict) -> None:
    """
    Updates victim information in the database with error handling.
    
    Args:
        victim_id (str): Unique identifier for the victim
        json_data (dict): Updated victim information
        
    Notes:
        - Attempts to update with provided status values
        - Falls back to default values if status update fails
        - Default values: rescue_status='pending', emergency_status='low_priority'
        
    Example:
        >>> victim_data = {
        ...     "location": {"latitude": 37.7749, "longitude": -122.4194},
        ...     "rescue_status": "in_progress",
        ...     "emergency_status": "high_priority"
        ... }
        >>> update_("victim123", victim_data)
    """
    # Get database reference
    ref = db.reference(f'rescue_team_dataset/', 
                      app=firebase_admin.get_app(name='RescueTeam_RealTimeDatabase'))
    
    # Update victim data
    ref.child(victim_id).update(json_data)
    
    try:
        # Try to update with provided status values
        update_time_and_status(
            ref, 
            victim_id, 
            time, 
            json_data.get('rescue_status'), 
            json_data.get('emergency_status')
        )
    except:
        # Fallback to default status values
        update_time_and_status(
            ref, 
            victim_id, 
            time, 
            'pending', 
            'low_priority'
        )

# Load JSON template for victim data
with open('configs/victim_json_template_flat.json', 'r') as f:
    json_template = json.load(f)
