
import streamlit as st
import time

from streamlit_geolocation import streamlit_geolocation
import random
from geopy.geocoders import Nominatim

location = None
start_time = time.time() 

st.title("Geolocation Streamlit App")
st.write("This app will get your location and show it on the map")
max_time = 10
location = streamlit_geolocation()
while location['latitude'] is None or location['latitude'] == "":
    time.sleep(0.1)
    time_left = max_time - (time.time() - start_time)
    st.write(f"Waiting for location access... Time left: {time_left:.2f} seconds")
    if time.time() - start_time > max_time:
        st.error("Location access timed out. Please try again later")
        break
time.sleep(2)
st.write(f"User location: {location}")
try:
    geolocator = Nominatim(user_agent="geoapiExercises")
    location = geolocator.reverse(f"{location['latitude']}, {location['longitude']}")
    st.warning(f"User location: {location}")
except:
    pass
