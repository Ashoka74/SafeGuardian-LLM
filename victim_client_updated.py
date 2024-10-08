from victim_tools.llm_utils import GeminiConfig, schema, victim_info_schema# tool_config_from_mode
from victim_tools.geolocation_data import geolocation_data
from victim_tools.rescue_data import get_rescue_data
from victim_tools.vital_data import update_victim_json
from victim_tools.json_cleaner import upload_victim_info

from victim_tools.audio_processing import process_audio, play_audio
from victim_tools.function_calling import provide_user_location
from victim_tools.state_manager import StateManager
from rescue_tools.fetch_vital_data import set_key, update_, json_template

from streamlit_geolocation import streamlit_geolocation

import time

import io
import base64
import json
import logging
import jsonschema
import os
import requests
from dotenv import load_dotenv

load_dotenv()

import datetime
import streamlit as st
state_manager = StateManager()
from typing import Dict, Any, List
import google.generativeai as genai
from audiorecorder import audiorecorder

from geopy.geocoders import Nominatim

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
gemini_api = os.getenv("gemini_api")
model_path = 'models/gemini-1.5-pro-exp-0827'  
response_type = 'application/json'
config = GeminiConfig(gemini_api, model_path, response_type)

def get_location_from_wifi() -> str:
    try:
        return geolocation_data(os.getenv('geolocator_api'))
    except Exception as e:
        return f"Error occurred: {e}"

# Streamlit setup
st.set_page_config(page_title="Natural Hazard Rescue Bot💬", layout="wide", page_icon="🚑")
st._config.set_option("theme.base", "dark")
st._config.set_option("theme.backgroundColor", "black")
st._config.set_option("runner.fastReruns", "false")

# Initialize state

# # Latitude
# if "latitude" not in st.session_state:
#     st.session_state['latitude'] = None

# if "longitude" not in st.session_state:
#     st.session_state['longitude'] = None

# JSON Schema
if "json_template" not in st.session_state:
    st.session_state['json_template'] = json_template

# Updated JSON Schema
if "victim_info" not in st.session_state:
    st.session_state.victim_info = json_template
if "victim_number" not in st.session_state:
    st.session_state['victim_number'] = set_key(st.session_state['victim_info'])
if "victim_history" not in st.session_state:
    st.session_state.victim_history = {}

# Function calling definitions
function_calling = {
    #'get_rescue_data': get_rescue_data,
    #'get_location': provide_user_location,
    #'get_victim_location': get_location_from_wifi,
    # Add more functions here!
}


system_instructions = "You are a post-disaster bot. Help victims while collecting valuable data for intervention teams. Your aim is to complete this template : {victim_info} Only return JSON output when calling function."

#tool_config = tool_config_from_mode(mode='any', fns=function_calling.keys())



# Gemini setup
model = genai.GenerativeModel(
    config.model_path,
    tools=list(function_calling.values()),
    system_instruction=system_instructions,
    safety_settings=config.safety,
    #tool_config = tool_config
    )

# from nexa.gguf import NexaTextInference

# model_path = "gemma-1.1-2b-instruct:q4_0"

# inference = NexaTextInference(
#     model_path=model_path,
#     local_path=None,
#     stop_words=[],
#     temperature=0.7,
#     max_new_tokens=512,
#     top_k=50,
#     top_p=0.9,
#     profiling=True
# )



# initialize chat
chat = model.start_chat(enable_automatic_function_calling=True)
# send a message
#chat.send_message('Hello', stream=True)

#output = chat.send_message('hello')



# initialize streamlit components
def main():
    st.title("💬 Natural Hazard Rescue App ⚠️🚑")
    st.write("This bot is designed to help victims of natural disasters by providing support and information. It can also collect valuable data for intervention teams.")


    # # create 3 columns
    # left, middle, right = st.columns([.5, .1, .4])
    # # Chat input and display
    # with left:
    #     chat_container(height=820)

    # # Victim information display
    # with right:
    #     display_victim_info()

    chat_container(820)
    display_victim_info()

# create chat container
def chat_container(height: int):
    with st.container(height=height, border=True):
        left_, right_ = st.columns([.8, .2])
        with right_:
            # get prompt from audio
            audio = audiorecorder("🎤", "stop", show_visualizer=False)
        with left_:  
            # get prompt from text  
            prompt = st.chat_input("Enter Query here") or process_audio(audio)

        if state_manager.get_conversation_history() == "":
            introduction_str = "Hi, I am SafeGuardianAI. I am here to provide you with support, as well as informing rescue teams of your vital status. Can you speak?"# Please press the button to let me access your location for most accurate assistance."
            try:
                play_audio(introduction_str)
            except:
                pass
            state_manager.add_message(role="assistant", content=introduction_str)

        location = streamlit_geolocation()
        if location['latitude'] is not None:
            try:
                geolocator = Nominatim(user_agent="geoapiExercises")
                location_ = geolocator.reverse(f"{location['latitude']}, {location['longitude']}")
                st.session_state['victim_info']['location'] = location
                st.session_state['victim_info']['location']['details'] = location_.address
                state_manager.add_message(role="assistant", content=f"longitude, latitude, details: {location['longitude']}, {location['latitude'], location_.address}")
                #st.warning(f"User location: {location}")
            except:
                try:
                    state_manager.add_message(role="assistant", content=f"User location: {location}")
                    st.session_state['victim_info']['location'] = location
                except Exception as e:
                    logger.error(f"Error updating victim info: {e}")
                    state_manager.add_message(role="assistant", content="Error updating victim info.")

        if prompt:
            state_manager.add_message(role="user", content=prompt)
            try:
                # LLM inference
                response = generate_response(prompt)
            except Exception as e:
                logger.error(f"Error generating response: {e}")
                # try to call function with args manually 
                response = generate_manual_response(prompt)
            state_manager.add_message("assistant", response)
            process_json_response(response)
        state_manager.display_messages()


def display_victim_info():
    st.write("Parsed Informations:\n\n", st.session_state.victim_info) 
    # send data to FireBase
    try:
        update_(st.session_state['victim_number'], st.session_state['victim_info'])
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.success(f"{time}\nID: {st.session_state['victim_number']} \n Your data has been sent to the Rescue Team.")
    except Exception as e:
        logger.error(f"Error sending data to Firebase: {e}")
        st.warning("{time}\nError sending data to the Rescue Team.")


def generate_response(user_input: str) -> str:
        if st.session_state.victim_info != json_template:
            try:
                informations_collected = {k: v for k, v in st.session_state.victim_history.items() if v is not None and v != ""}
                string_informations_collected = ", ".join([f"{k}: {v}" for k, v in informations_collected.items()])
                response = chat.send_message(f"You already collected my {string_informations_collected}.{user_input}")
                print(response)
            except Exception as e:
                print(e)
                response = chat.send_message(user_input)
        else:
            response = chat.send_message(user_input)
            print(response)
        try:
            return response.text
        except AttributeError:
            print("Google model not available, using Groq instead")
            function_calls = extract_function_calls(response)
            for function_call in function_calls:
                for function_name, function_args in function_call.items():
                    return globals()[function_name](**function_args)

       

def generate_manual_response(user_input: str) -> str:
    response = chat.send_message(user_input)
    for part in response.candidates[0].content.parts:
        if response.candidates[0].content.parts[0].function_call:
            function_name = response.candidates[0].content.parts[0].function_call.name
            function_args = response.candidates[0].content.parts[0].function_call.args
            with st.status(f"Running function {function_name}...") as status_text:
                try:
                    function_args_dict = json.loads(function_args)
                except json.JSONDecodeError:
                    logger.error(f"Error decoding JSON: {function_args}")
                    return "Error processing function arguments."

                result = globals()[function_name](**function_args_dict)
                # add to existing instead of replacing
                st.session_state.victim_info = result
                #st.session_state.victim_history = {**st.session_state.victim_history, **result}

                return response.text
        else:
            return response.text


def extract_function_calls(response) -> List[Dict[str, Any]]:
    function_calls = []
    if response.candidates[0].function_calls:
        for function_call in response.candidates[0].function_calls:
            function_call_dict = {function_call.name: {}}
            for key, value in function_call.args.items():
                function_call_dict[function_call.name][key] = value
            function_calls.append(function_call_dict)
    return function_calls


def process_and_upload_victim_info(response: str, schema: Dict[str, Any]):
    try:
        play_audio(response)
    except Exception as e:
        logger.error(f"Error playing audio: {e}")

    if '```json' in response:
        json_str = response.split('```json')[1].split('```')[0]
        try:
            json_data = json.loads(json_str)
            if 'message' in json_data and len(json_data) == 1:
                return json_data['message']
            else:
                # Consider adding JSON validation here
                st.session_state['victim_info'] = json_data
                st.session_state['victim_info']['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info("Victim info updated successfully")
                return json_str
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            st.warning("Invalid JSON format in response.")
    else:
        logger.info("No JSON block found in response.")
        return None  # Explicitly return None

def process_json_response(response: str):
    # check if response is JSON
    try:
        play_audio(response)
    except Exception as e:
        logger.error(f"Error playing audio: {e}")
    if '```json' in response:
        if 'message' in json.loads(response.split('```json')[1].split('```')[0]) and len(json.loads(response.split('```json')[1].split('```')[0])) == 1:          
            return str(response.split('```json')[1].split('```')[0]['message'])
        else:
            try:
                upload_victim_info(update_victim_json(new_infos=response), schema)
            except:
                st.warning("Error updating victim info.")
            
main()