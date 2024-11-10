# location_services.py


"""
Location Services Module for Streamlit Applications
================================================

This module provides location-based services and utilities for Streamlit applications,
specializing in real-time user location acquisition with timeout handling.

Key Features:
    - Real-time geolocation retrieval
    - Timeout management for location requests
    - Streamlit integration for user feedback
    - Support for reverse geocoding (commented)
    - Gmail account integration capabilities (commented)

Dependencies:
    - streamlit_geolocation: For browser-based location access
    - geopy.geocoders: For reverse geocoding capabilities
    - streamlit: For UI components and user interaction
    - time: For timeout management
    - logging: For error tracking and debugging

Configuration:
    Uses default logging configuration for error tracking.
    Nominatim setup available for reverse geocoding (currently commented).
"""

from streamlit_geolocation import streamlit_geolocation
from geopy.geocoders import Nominatim
import logging
from googleapiclient.discovery import build 
import streamlit as st
import time

# Initialize logger for this module
logger = logging.getLogger(__name__)

def provide_user_location(max_time: float = 10) -> str:
    """
    Retrieves user's geolocation through browser API with timeout handling.
    
    Continuously attempts to access user location until successful or timeout occurs.
    Provides real-time feedback through Streamlit UI components.
    
    Args:
        max_time (float, optional): Maximum time in seconds to wait for location.
            Defaults to 10 seconds.
    
    Returns:
        dict: Location data containing:
            - latitude: User's latitude
            - longitude: User's longitude
            Or None if location access fails
    
    Example:
        >>> location = provide_user_location(max_time=15)
        >>> if location:
        ...     print(f"Lat: {location['latitude']}, Long: {location['longitude']}")
    
    Notes:
        - Uses browser's geolocation API through streamlit_geolocation
        - Provides real-time countdown in Streamlit UI
        - Includes 2-second delay after location acquisition
        - Has commented code for reverse geocoding using Nominatim
        
    UI Feedback:
        - Shows countdown timer during location access
        - Displays error message on timeout
        - Shows final location when successful
    """
    location = None
    start_time = time.time() 

    # Initial location request
    location = streamlit_geolocation.streamlit_geolocation()
    
    # Wait for location with timeout
    while location['latitude'] is None or location['latitude'] == "":
        time.sleep(0.1)
        time_left = max_time - (time.time() - start_time)
        st.write(f"Waiting for location access... Time left: {time_left:.2f} seconds")
        
        if time.time() - start_time > max_time:
            st.error("Location access timed out. Please try again later")
            break
    
    # Add slight delay for stability
    time.sleep(2)
    
    # Display result
    st.write(f"User location: {location}")
    
    # Commented reverse geocoding functionality
    # try:
    #     geolocator = Nominatim(user_agent="geoapiExercises")
    #     location = geolocator.reverse(f"{location['latitude']}, {location['longitude']}")
    #     st.warning(f"User location: {location}")
    # except:
    #     pass
    # response = ' - '.join([location['latitude'], location['longitude']])
    # return response

"""
Commented Gmail Integration Function
==================================

def get_gmail_account() -> str:
    '''
    Retrieves Gmail account information using Google API.
    
    Requires:
        - token.json file with valid credentials
        - Gmail API access
        
    Returns:
        str: Email address of the authenticated user
        
    Note: Currently commented out due to pending implementation/security review
    '''
    store = file.Storage('token.json') 
    creds = store.get() 
    service = build('gmail', 'v1', credentials=creds) 
    results = service.users().getProfile(userId='sinanrobillard@gmail.com').execute()
    return results['emailAddress']
"""
