# location_services.py

from streamlit_geolocation import streamlit_geolocation
from geopy.geocoders import Nominatim
import logging
from googleapiclient.discovery import build 
import streamlit as st
import time


logger = logging.getLogger(__name__)

def provide_user_location(max_time: float = 10) -> str:
    location = None
    start_time = time.time() 
    try:
        location = streamlit_geolocation()
        while location['latitude'] is None or location['latitude'] == "":
            time.sleep(0.1)
            time_left = max_time - (time.time() - start_time)
            st.write(f"Waiting for location access... Time left: {time_left:.2f} seconds")
            if time.time() - start_time > max_time:
                st.error("Location access timed out. Please try again later")
                break
        time.sleep(2)
        response = ' - '.join([location['latitude'], location['longitude']])
        return response
    except Exception as e:
        st.write(f'Error processing {e}')

  

# def get_gmail_account() -> str:
#     store = file.Storage('token.json') 
#     creds = store.get() 
#     service = build('gmail', 'v1', credentials=creds) 
#     results = service.users().getProfile(userId='sinanrobillard@gmail.com').execute()
#     return results['emailAddress']