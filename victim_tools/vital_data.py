from typing import List, Tuple, Optional, Dict, Any
import streamlit as st
import google.generativeai as genai
import json
import os
import dotenv
from victim_tools.llm_utils import schema

dotenv.load_dotenv()

gemini_api = os.getenv("gemini_api")


def update_victim_json(new_infos: Optional[Dict[str, Any]]):
    json_template = st.session_state.get('json_template', {})
    history_infos = st.session_state.get('victim_info', {})
    prompt = f"Update the JSON structure: {schema}\n\n with accurate informations based on history: {history_infos}\n\n and new informations: {new_infos}\n\n. Output should be a JSON file. Fit new information in the main structure of the template [{json_template.keys()}]. Leave blank (e.g.""), when there is no information. Do not overwrite existing information provided, unless it's to update it into something more informative. NEVER replace existing information with blank values! Ask follow-up questions to keep filling the json file, but in a natural way and prioritizing the most importants ones for rescue. Always update emergency_status! Output:"
    genai.configure(api_key=gemini_api)
    model = genai.GenerativeModel("gemini-1.5-flash", generation_config={"response_mime_type":"application/json"})
    response = model.generate_content(prompt)
    return response.text 