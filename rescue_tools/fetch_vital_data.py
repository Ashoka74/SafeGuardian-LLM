import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
import json
import os
import datetime
time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

cred = credentials.Certificate("rescue_tools/disasterrescueai-firebase-adminsdk.json")

try:
    firebase_admin.initialize_app(credential=cred,options={'databaseURL': 'https://disasterrescueai-default-rtdb.firebaseio.com'}, name='RescueTeam_RealTimeDatabase')
except:
    pass

db = firebase_admin.db

def set_key(json_data):
    ref = db.reference('rescue_team_dataset', app=firebase_admin.get_app(name='RescueTeam_RealTimeDatabase'))
    # Generate a unique key
    new_key = ref.push().key
    # Add the data with the unique key
    ref.child(new_key).set(json_data)
    return new_key


def update_time_and_status(ref, victim_id, time, rescue_status, emergency_status):
    ref.child(victim_id).update({'last_updated': time, 'rescue_status': rescue_status, 'emergency_status': emergency_status})

def update_(victim_id, json_data):
    # Check if key exists in the database
    ref = db.reference(f'rescue_team_dataset/', app=firebase_admin.get_app(name='RescueTeam_RealTimeDatabase'))
    # try to get emergency_status
    ref.child(victim_id).update(json_data)
    try:
        update_time_and_status(ref, victim_id, time, json_data.get('rescue_status'), json_data.get('emergency_status'))
    except:
        update_time_and_status(ref, victim_id, time, 'pending', 'low_priority')


with open('configs/victim_json_template_flat.json', 'r') as f:
    json_template = json.load(f)

