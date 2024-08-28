from typing import List, Tuple, Optional, Dict, Any
import streamlit as st
import google.generativeai as genai
import json
import os
import dotenv
from victim_tools.llm_utils import schema, victim_info_schema

dotenv.load_dotenv()

gemini_api = os.getenv("gemini_api")


# def update_victim_json(new_infos: Optional[Dict[str, Any]]):
#     json_template = st.session_state.get('json_template', {})
#     history_infos = st.session_state.get('victim_info', {})
#     prompt = f"Update the JSON structure: {schema}\n\n with accurate informations based on history: {history_infos}\n\n and new informations: {new_infos}\n\n. Output should be a JSON file. Fit new information in the main structure of the template [{json_template.keys()}]. Leave blank (e.g.""), when there is no information. Do not overwrite existing information provided, unless it's to update it into something more informative. NEVER replace existing information with blank values! Ask follow-up questions to keep filling the json file, but in a natural way and prioritizing the most importants ones for rescue. Always update emergency_status [unknown, stable, urgent, very_urgent, critical], but keep it low by default. Output:"
#     genai.configure(api_key=gemini_api)
#     model = genai.GenerativeModel("gemini-1.5-flash-8b-exp-0827", generation_config={"response_mime_type":"application/json", "response_schema":victim_info_schema})
#     response = model.generate_content(prompt)
#     return response.text 


import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Helicone and Groq configuration
helicone_api_key = os.getenv('helicone_api')
groq_api_key = os.getenv('groq_api')

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {groq_api_key}',
    'Helicone-Auth': f"Bearer {helicone_api_key}",
    'Helicone-Target-URL': 'https://api.groq.com',
}

url = "https://groq.helicone.ai/openai/v1/chat/completions"

def send_message(message, system_instruction=None):
    messages = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": message})

    data = {
        "model": "llama-3.1-70b-versatile",  # or whichever model you're using
        #"model": "llama-3.1-8b-instant",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2048,
        "stream": False,
    }

    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()



def update_victim_json(new_infos: Optional[Dict[str, Any]]):
    json_template = st.session_state.get('json_template', {})
    history_infos = st.session_state.get('victim_info', {})
    
    prompt = f"Update the JSON structure: {schema}\n\n with accurate informations based on history: {history_infos}\n\n and new informations: {new_infos}\n\n. Output should be a JSON file. Fit new information in the main structure of the template [{json_template.keys()}]. Leave blank (e.g.""), when there is no information. Do not overwrite existing information provided, unless it's to update it into something more informative. NEVER replace existing information with blank values! Ask follow-up questions to keep filling the json file, but in a natural way and prioritizing the most importants ones for rescue. Always update emergency_status [unknown, stable, urgent, very_urgent, critical], but keep it low by default. Output:"

    try:
        response = send_message(prompt)
        content = response['choices'][0]['message']['content']
        
        try:
            return content.split('```json')[1].split('```')[0]
        except json.JSONDecodeError:
            print("Failed to parse response as JSON. Raw response:")
            print(content)
            return None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None