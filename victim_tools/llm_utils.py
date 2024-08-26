
import streamlit as st
from google.generativeai.types import content_types #uncompatible version with streamlit
from collections.abc import Iterable
import time
from sodapy import Socrata
import json
import re
from IPython.display import display
from IPython.display import Markdown
from geopy.geocoders import Nominatim

# import ABC and abstract
from abc import ABC, abstractmethod
from enum import Enum

import pathlib
import textwrap
import requests

import google.generativeai as genai

from IPython.display import display
from IPython.display import Markdown
from typing import List, Tuple, Optional, Dict, Any



class GeminiConfig:
    def __init__(self, gemini_api, model_path, response_type):
        self.gemini_api = gemini_api
        self.model_path = model_path
        self.response_type = response_type

        self.generation_config = genai.GenerationConfig(response_mime_type=self.response_type)
        genai.configure(api_key=self.gemini_api)
        self.model = genai.GenerativeModel(self.model_path, generation_config=self.generation_config)
        self.safety = [
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            }
        ]


def tool_config_from_mode(mode: str, fns: Iterable[str] = ()):
    """Create a tool config with the specified function calling mode."""
    return content_types.to_tool_config(
        {"function_calling_config": {"mode": mode, "allowed_function_names": fns}}
    )



# def get_ip():
#     response = requests.get('https://api.ipify.org?format=json')
#     return response.json()["ip"]

# def get_location_from_ip(ip_address):
#     response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
#     location_data = {
#         "latitude": response.get("latitude"),
#         "longitude": response.get("longitude"),
#     }
#     return location_data

def get_user_location_fn(lat, lon):
    geolocator = Nominatim(user_agent="streamlit_geolocation_app")
    location = geolocator.reverse(f"{lat},{lon}")
    return location

def process_location(user_location):
    try:
        if user_location:
            latitude = user_location.get("latitude")
            longitude = user_location.get("longitude")
            loc_req = get_user_location_fn(latitude, longitude)
            city = loc_req.raw['address'].get('city', 'N/A')
            county = loc_req.raw['address'].get('county', 'N/A')
            state = loc_req.raw['address'].get('state', 'N/A')
            country = loc_req.raw['address'].get('country', 'N/A')
            return f"City: {city}, County: {county}, State: {state}, Country: {country}"
        else:
            return "No location data received."
    except Exception as e:
        return f"Error: {str(e)}"
    
def replace_none_with_default(data, default_value=None):
    """
    Recursively replaces all None values in a dictionary with the specified default value.

    Args:
        data: The dictionary to process.
        default_value: The value to replace None with. Defaults to None.

    Returns:
        The modified dictionary with None values replaced.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = replace_none_with_default(value, default_value)
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = replace_none_with_default(item, default_value)
    elif data is None:
        return default_value
    return data



def sanitize_json(json_data):
    """
    Sanitizes JSON data by handling null values and potential syntax errors.

    Args:
        json_data: The JSON data to sanitize (as a string or a dictionary).

    Returns:
        The sanitized JSON data as a Python dictionary.
    """
    try:
        if isinstance(json_data, str):
            data = json.loads(json_data)
        elif isinstance(json_data, dict):
            data = json_data
        else:
            raise ValueError("Invalid input type. Must be a JSON string or a dictionary.")

        # Replace None and null values with a default value (e.g., an empty string)
        sanitized_data = replace_none_with_default(data, default_value="")
        return sanitized_data

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        # Handle the error appropriately, e.g., return an empty dictionary or raise an exception
        return {}

# Example usage (assuming the provided JSON is in a variable called `json_string`)

def fix_json(json_string):
    # Remove any leading/trailing whitespace and 'json' prefix
    json_string = json_string.strip()
    json_string = re.sub(r'^json\s*', '', json_string, flags=re.IGNORECASE)
    
    # Remove any trailing commas before closing braces or brackets
    json_string = re.sub(r',\s*([}\]])', r'\1', json_string)
    
    # Add missing commas between key-value pairs
    json_string = re.sub(r'"\s*}\s*"', '", "', json_string)
    json_string = re.sub(r'"\s*]\s*"', '"], "', json_string)
    
    # Ensure all keys are properly quoted
    json_string = re.sub(r'([{,])\s*(\w+):', r'\1 "\2":', json_string)
    
    # Replace single quotes with double quotes
    json_string = json_string.replace("'", '"')
    
    # Ensure proper formatting for empty strings and arrays
    json_string = re.sub(r':\s*""', ': ""', json_string)
    json_string = re.sub(r':\s*\[\]', ': []', json_string)
    
    # Try to parse the JSON
    try:
        parsed_json = json.loads(json_string)
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None


schema = {
  "type": "object",
  "properties": {
    "victim_info": {
      "type": "object",
      "properties": {
        "id": {"type": "string"},
        "emergency_status": {
                "type": "string",
                "enum": ["critical", "very_urgent", "urgent", "stable", "unknown"]
                },       
        "location": {
          "type": "object",
          "properties": {
            "lat": {"type": "number"},
            "lon": {"type": "number"},
            "details": {"type": "string"},
            "nearest_landmark": {"type": "string"}
          },
          "required": ["lat", "lon", "details", "nearest_landmark"]
        },
        "personal_info": {
          "type": "object",
          "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer"},
            "gender": {"type": "string"},
            "language": {"type": "string"},
            "physical_description": {"type": "string"}
          },
          "required": ["name", "age", "gender", "language", "physical_description"]
        },
        "medical_info": {
          "type": "object",
          "properties": {
            "injuries": {"type": "array", "items": {"type": "string"}},
            "pain_level": {"type": "integer"},
            "medical_conditions": {"type": "array", "items": {"type": "string"}},
            "medications": {"type": "array", "items": {"type": "string"}},
            "allergies": {"type": "array", "items": {"type": "string"}},
            "blood_type": {"type": "string"}
          },
          "required": ["injuries", "pain_level", "medical_conditions", "medications", "allergies", "blood_type"]
        },
        "situation": {
          "type": "object",
          "properties": {
            "disaster_type": {"type": "string"},
            "immediate_needs": {"type": "array", "items": {"type": "string"}},
            "trapped": {"type": "boolean"},
            "mobility": {"type": "string"},
            "nearby_hazards": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["disaster_type", "immediate_needs", "trapped", "mobility", "nearby_hazards"]
        },
        "contact_info": {
          "type": "object",
          "properties": {
            "phone": {"type": "string"},
            "email": {"type": "string"},
            "emergency_contact": {
              "type": "object",
              "properties": {
                "name": {"type": "string"},
                "relationship": {"type": "string"},
                "phone": {"type": "string"}
              },
              "required": ["name", "relationship", "phone"]
            }
          },
          "required": ["phone", "email", "emergency_contact"]
        },
        "resources": {
          "type": "object",
          "properties": {
            "food_status": {"type": "string"},
            "water_status": {"type": "string"},
            "shelter_status": {"type": "string"},
            "communication_devices": {"type": "array", "items": {"type": "string"}}
          },
          "required": ["food_status", "water_status", "shelter_status", "communication_devices"]
        },
        "rescue_info": {
          "type": "object",
          "properties": {
            "last_contact": {"type": "string"},
            "rescue_team_eta": {"type": "string"},
            "special_rescue_needs": {"type": "string"}
          },
          "required": ["last_contact", "rescue_team_eta", "special_rescue_needs"]
        },
        "environmental_data": {
          "type": "object",
          "properties": {
            "temperature": {"type": "number"},
            "humidity": {"type": "number"},
            "air_quality": {"type": "string"},
            "weather": {"type": "string"}
          },
          "required": ["temperature", "humidity", "air_quality", "weather"]
        },
        "device_data": {
          "type": "object",
          "properties": {
            "battery_level": {"type": "integer"},
            "network_status": {"type": "string"}
          },
          "required": ["battery_level", "network_status"]
        },
        "social_info": {
          "type": "object",
          "properties": {
            "group_size": {"type": "integer"},
            "dependents": {"type": "integer"},
            "nearby_victims_count": {"type": "integer"},
            "can_communicate_verbally": {"type": "boolean"}
          },
          "required": ["group_size", "dependents", "nearby_victims_count", "can_communicate_verbally"]
        },
        "psychological_status": {
          "type": "object",
          "properties": {
            "stress_level": {"type": "string"},
            "special_needs": {"type": "string"}
          },
          "required": ["stress_level", "special_needs"]
        }
      },
      "required": ["id", "emergency_status", "location", "personal_info", "medical_info", "situation", "contact_info", "resources", "rescue_info", "environmental_data", "device_data", "social_info", "psychological_status"]
    }
  },
  "required": ["victim_info"]
}


victim_info_schema = genai.protos.Schema(
    type=genai.protos.Type.OBJECT,
    properties={
        'id': genai.protos.Schema(type=genai.protos.Type.STRING),
        'emergency_status': genai.protos.Schema(type=genai.protos.Type.STRING),
        'location': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'lat': genai.protos.Schema(type=genai.protos.Type.NUMBER),
                'lon': genai.protos.Schema(type=genai.protos.Type.NUMBER),
                'details': genai.protos.Schema(type=genai.protos.Type.STRING),
                'nearest_landmark': genai.protos.Schema(type=genai.protos.Type.STRING)
            }
        ),
        'personal_info': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'name': genai.protos.Schema(type=genai.protos.Type.STRING),
                'age': genai.protos.Schema(type=genai.protos.Type.INTEGER),
                'gender': genai.protos.Schema(type=genai.protos.Type.STRING),
                'language': genai.protos.Schema(type=genai.protos.Type.STRING),
                'physical_description': genai.protos.Schema(type=genai.protos.Type.STRING)
            }
        ),
        'medical_info': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'injuries': genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING)),
                'pain_level': genai.protos.Schema(type=genai.protos.Type.INTEGER),
                'medical_conditions': genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING)),
                'medications': genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING)),
                'allergies': genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING)),
                'blood_type': genai.protos.Schema(type=genai.protos.Type.STRING)
            }
        ),
        'situation': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'disaster_type': genai.protos.Schema(type=genai.protos.Type.STRING),
                'immediate_needs': genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING)),
                'trapped': genai.protos.Schema(type=genai.protos.Type.BOOLEAN),
                'mobility': genai.protos.Schema(type=genai.protos.Type.STRING),
                'nearby_hazards': genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING))
            }
        ),
        'contact_info': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'phone': genai.protos.Schema(type=genai.protos.Type.STRING),
                'email': genai.protos.Schema(type=genai.protos.Type.STRING),
                'emergency_contact': genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={
                        'name': genai.protos.Schema(type=genai.protos.Type.STRING),
                        'relationship': genai.protos.Schema(type=genai.protos.Type.STRING),
                        'phone': genai.protos.Schema(type=genai.protos.Type.STRING)
                    }
                )
            }
        ),
        'resources': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'food_status': genai.protos.Schema(type=genai.protos.Type.STRING),
                'water_status': genai.protos.Schema(type=genai.protos.Type.STRING),
                'shelter_status': genai.protos.Schema(type=genai.protos.Type.STRING),
                'communication_devices': genai.protos.Schema(type=genai.protos.Type.ARRAY, items=genai.protos.Schema(type=genai.protos.Type.STRING))
            }
        ),
        'rescue_info': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'last_contact': genai.protos.Schema(type=genai.protos.Type.STRING),
                'rescue_team_eta': genai.protos.Schema(type=genai.protos.Type.STRING),
                'special_rescue_needs': genai.protos.Schema(type=genai.protos.Type.STRING)
            }
        ),
        'environmental_data': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'temperature': genai.protos.Schema(type=genai.protos.Type.NUMBER),
                'humidity': genai.protos.Schema(type=genai.protos.Type.NUMBER),
                'air_quality': genai.protos.Schema(type=genai.protos.Type.STRING),
                'weather': genai.protos.Schema(type=genai.protos.Type.STRING)
            }
        ),
        'device_data': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'battery_level': genai.protos.Schema(type=genai.protos.Type.INTEGER),
                'network_status': genai.protos.Schema(type=genai.protos.Type.STRING)
            }
        ),
        'social_info': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'group_size': genai.protos.Schema(type=genai.protos.Type.INTEGER),
                'dependents': genai.protos.Schema(type=genai.protos.Type.INTEGER),
                'nearby_victims_count': genai.protos.Schema(type=genai.protos.Type.INTEGER),
                'can_communicate_verbally': genai.protos.Schema(type=genai.protos.Type.BOOLEAN)
            }
        ),
        'psychological_status': genai.protos.Schema(
            type=genai.protos.Type.OBJECT,
            properties={
                'stress_level': genai.protos.Schema(type=genai.protos.Type.STRING),
                'special_needs': genai.protos.Schema(type=genai.protos.Type.STRING)
            }
        )
    }
)

parameters_schema = genai.protos.Schema(
    type=genai.protos.Type.OBJECT,
    properties={
        'victim_info': victim_info_schema
    }
)

add_victim_info = genai.protos.FunctionDeclaration(
    name="add_victim_info",
    description=textwrap.dedent("""
        Adds victim information to the database.
    """),
    parameters=parameters_schema
)


import jsonschema
from jsonschema import validate, Draft7Validator

from jsonschema import Draft7Validator
from typing import Any, Dict, List, Union


def fix_json_schema(instance: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempts to fix the JSON based on the schema.
    
    Args:
        instance (Dict[str, Any]): The JSON instance to fix.
        schema (Dict[str, Any]): The JSON schema to validate against.
    
    Returns:
        Dict[str, Any]: The fixed JSON instance.
    """
    validator = Draft7Validator(schema)
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)
    
    for error in errors:
        path = list(error.path)
        current = instance
        
        # Navigate to the correct location in the instance
        for key in path[:-1]:
            if key not in current:
                current[key] = {} if isinstance(current, dict) else []
            current = current[key]
        
        if error.validator == 'required':
            if isinstance(current, dict):
                for prop in error.validator_value:
                    if prop not in current:
                        current[prop] = get_default_value(schema['properties'][prop])
        elif error.validator == 'type':
            key = path[-1] if path else None
            if key is not None:
                current[key] = coerce_type(current[key], error.validator_value)
        elif error.validator == 'additionalProperties' and not error.validator_value:
            if isinstance(current, dict):
                allowed_properties = set(schema.get('properties', {}).keys())
                for key in list(current.keys()):
                    if key not in allowed_properties:
                        del current[key]
        # Add more error handling cases as needed

    return instance


def get_default_value(prop_schema: Dict[str, Any]) -> Any:
    """
    Returns a default value based on the property schema.
    
    Args:
        prop_schema (Dict[str, Any]): The schema for a specific property.
    
    Returns:
        Any: A default value that matches the schema.
    """
    if 'default' in prop_schema:
        return prop_schema['default']
    elif 'type' in prop_schema:
        return get_type_default(prop_schema['type'])
    elif 'anyOf' in prop_schema:
        return get_default_value(prop_schema['anyOf'][0])
    elif 'oneOf' in prop_schema:
        return get_default_value(prop_schema['oneOf'][0])
    else:
        return None

def get_type_default(type_: Union[str, List[str]]) -> Any:
    """
    Returns a default value for a given type or list of types.
    
    Args:
        type_ (Union[str, List[str]]): The type or list of types.
    
    Returns:
        Any: A default value that matches the type.
    """
    if isinstance(type_, list):
        return get_type_default(type_[0])
    
    type_defaults = {
        'string': '',
        'integer': 0,
        'number': 0.0,
        'boolean': False,
        'array': [],
        'object': {}
    }
    return type_defaults.get(type_, None)

def coerce_type(value: Any, target_type: str) -> Any:
    """
    Attempts to coerce a value to the target type.
    
    Args:
        value (Any): The value to coerce.
        target_type (str): The desired type.
    
    Returns:
        Any: The coerced value.
    """
    if target_type == 'string':
        return str(value)
    elif target_type == 'integer':
        return int(float(value))
    elif target_type == 'number':
        return float(value)
    elif target_type == 'boolean':
        return bool(value)
    elif target_type == 'array':
        return [value] if not isinstance(value, list) else value
    elif target_type == 'object':
        return {} if not isinstance(value, dict) else value
    else:
        return value