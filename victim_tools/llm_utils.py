# Import necessary libraries
import streamlit as st
from google.generativeai.types import content_types  # Note: This version may be incompatible with Streamlit
from collections.abc import Iterable  # For working with iterable objects
import time
from sodapy import Socrata  # Socrata client for open data APIs
import json  # JSON library for handling JSON data
import re  # Regular expressions for string manipulation
from IPython.display import display, Markdown  # For displaying markdown in Jupyter environments
from geopy.geocoders import Nominatim  # For geolocation services

# Import abstract base class utilities and enumeration
from abc import ABC, abstractmethod
from enum import Enum

# Import additional libraries for handling paths, text formatting, and HTTP requests
import pathlib
import textwrap
import requests

# Import Google Generative AI client
import google.generativeai as genai

# Import additional display utilities for Jupyter environments
from typing import List, Tuple, Optional, Dict, Any

# Define a configuration class for Gemini AI settings
class GeminiConfig:
    def __init__(self, gemini_api, model_path, response_type):
        """
        Initialize the GeminiConfig with API key, model path, and response type.

        Args:
            gemini_api (str): API key for accessing the Gemini API.
            model_path (str): Path to the model to use.
            response_type (str): Expected response type from the model.
        """
        self.gemini_api = gemini_api
        self.model_path = model_path
        self.response_type = response_type

        # Set up configuration for the generation model with specified response type
        self.generation_config = genai.GenerationConfig(response_mime_type=self.response_type)
        
        # Configure the generative AI client with the provided API key
        genai.configure(api_key=self.gemini_api)
        
        # Initialize the generative model with the specified model path and configuration
        self.model = genai.GenerativeModel(self.model_path, generation_config=self.generation_config)
        
        # Define safety settings to prevent specific types of harmful content in responses
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

# Function to create a tool configuration based on mode
def tool_config_from_mode(mode: str, fns: Iterable[str] = ()):
    """
    Create a tool configuration with the specified function-calling mode.

    Args:
        mode (str): The mode for function calling (e.g., 'manual', 'auto').
        fns (Iterable[str]): List of allowed function names to call.

    Returns:
        ToolConfig: The tool configuration for the specified mode and allowed functions.
    """
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

def get_user_location_fn(lat, lon):
    """
    Fetches location details for given latitude and longitude coordinates.

    Args:
        lat (float): Latitude of the user's location.
        lon (float): Longitude of the user's location.

    Returns:
        Location: A geolocation object containing address details.
    """
    geolocator = Nominatim(user_agent="streamlit_geolocation_app")  # Initialize geolocator with a user agent
    location = geolocator.reverse(f"{lat},{lon}")  # Reverse geocode to get location details from coordinates
    return location

def process_location(user_location):
    """
    Processes the user location object to extract city, county, state, and country.

    Args:
        user_location (dict): A dictionary with 'latitude' and 'longitude' keys.

    Returns:
        str: A formatted string with city, county, state, and country details.
    """
    try:
        if user_location:
            # Extract latitude and longitude from user-provided location dictionary
            latitude = user_location.get("latitude")
            longitude = user_location.get("longitude")
            loc_req = get_user_location_fn(latitude, longitude)  # Get location details from coordinates
            
            # Retrieve address components with fallback values if missing
            city = loc_req.raw['address'].get('city', 'N/A')
            county = loc_req.raw['address'].get('county', 'N/A')
            state = loc_req.raw['address'].get('state', 'N/A')
            country = loc_req.raw['address'].get('country', 'N/A')
            return f"City: {city}, County: {county}, State: {state}, Country: {country}"
        else:
            return "No location data received."
    except Exception as e:
        return f"Error: {str(e)}"  # Handle any exceptions and return the error message

def replace_none_with_default(data, default_value=None):
    """
    Recursively replaces all None values in a dictionary with a specified default value.

    Args:
        data (dict or list): The data structure to process, typically a dictionary or list.
        default_value: The value to replace None with (default is None).

    Returns:
        dict or list: The modified data structure with None values replaced.
    """
    if isinstance(data, dict):
        # Replace None in each dictionary item
        for key, value in data.items():
            data[key] = replace_none_with_default(value, default_value)
    elif isinstance(data, list):
        # Replace None in each list item
        for i, item in enumerate(data):
            data[i] = replace_none_with_default(item, default_value)
    elif data is None:
        return default_value  # Replace None with the default value if found
    return data

def sanitize_json(json_data):
    """
    Sanitizes JSON data by handling null values and potential syntax errors.

    Args:
        json_data (str or dict): The JSON data to sanitize, as a string or dictionary.

    Returns:
        dict: The sanitized JSON data as a Python dictionary, or an empty dictionary if parsing fails.
    """
    try:
        # Load JSON data from string if necessary
        if isinstance(json_data, str):
            data = json.loads(json_data)
        elif isinstance(json_data, dict):
            data = json_data
        else:
            raise ValueError("Invalid input type. Must be a JSON string or a dictionary.")

        # Replace None values with an empty string or specified default
        sanitized_data = replace_none_with_default(data, default_value="")
        return sanitized_data

    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return {}  # Return an empty dictionary on decoding error

def fix_json(json_string):
    """
    Attempts to fix common syntax errors in a JSON string for proper parsing.

    Args:
        json_string (str): The JSON string with potential syntax issues.

    Returns:
        dict or None: Parsed JSON as a dictionary if successful, otherwise None.
    """
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
    
    # Try to parse the cleaned JSON string
    try:
        parsed_json = json.loads(json_string)
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return None  # Return None if parsing fails


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
from typing import Any, Dict, List, Union

def fix_json_schema(instance: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Attempts to fix the JSON instance so it conforms to the given schema by addressing validation errors.

    Args:
        instance (Dict[str, Any]): The JSON data to validate and potentially fix.
        schema (Dict[str, Any]): The JSON schema to validate against.

    Returns:
        Dict[str, Any]: The fixed JSON instance.
    """
    validator = Draft7Validator(schema)  # Initialize the validator with the provided schema
    errors = sorted(validator.iter_errors(instance), key=lambda e: e.path)  # Collect and sort validation errors
    
    for error in errors:
        path = list(error.path)  # Extract the path to the error within the JSON data
        current = instance  # Initialize navigation within the instance

        # Traverse the instance to reach the location of the error
        for key in path[:-1]:
            if key not in current:
                current[key] = {} if isinstance(current, dict) else []  # Add missing keys as empty dict or list
            current = current[key]
        
        # Handle specific types of validation errors
        if error.validator == 'required':
            if isinstance(current, dict):
                # For missing required properties, add them with default values
                for prop in error.validator_value:
                    if prop not in current:
                        current[prop] = get_default_value(schema['properties'][prop])
        
        elif error.validator == 'type':
            # If the value is of the wrong type, attempt to coerce it to the expected type
            key = path[-1] if path else None
            if key is not None:
                current[key] = coerce_type(current[key], error.validator_value)
        
        elif error.validator == 'additionalProperties' and not error.validator_value:
            # If additional properties are not allowed, remove them if they exist in the instance
            if isinstance(current, dict):
                allowed_properties = set(schema.get('properties', {}).keys())
                for key in list(current.keys()):
                    if key not in allowed_properties:
                        del current[key]
        # Additional error handling cases can be added here as needed

    return instance  # Return the modified (fixed) instance

def get_default_value(prop_schema: Dict[str, Any]) -> Any:
    """
    Provides a default value based on the property schema.

    Args:
        prop_schema (Dict[str, Any]): The schema for a specific property.

    Returns:
        Any: A default value that matches the schema's expected type.
    """
    if 'default' in prop_schema:
        return prop_schema['default']  # Use the schema-defined default if available
    elif 'type' in prop_schema:
        return get_type_default(prop_schema['type'])  # Get default based on type
    elif 'anyOf' in prop_schema:
        return get_default_value(prop_schema['anyOf'][0])  # Use the first valid option for 'anyOf' constraints
    elif 'oneOf' in prop_schema:
        return get_default_value(prop_schema['oneOf'][0])  # Use the first valid option for 'oneOf' constraints
    else:
        return None  # Return None if no default can be determined

def get_type_default(type_: Union[str, List[str]]) -> Any:
    """
    Returns a suitable default value for a specified type or list of types.

    Args:
        type_ (Union[str, List[str]]): The type (or list of types) for which a default value is needed.

    Returns:
        Any: A default value that matches the specified type.
    """
    if isinstance(type_, list):
        return get_type_default(type_[0])  # Use the default for the first type in the list

    # Define defaults for common JSON data types
    type_defaults = {
        'string': '',
        'integer': 0,
        'number': 0.0,
        'boolean': False,
        'array': [],
        'object': {}
    }
    return type_defaults.get(type_, None)  # Return the default value for the specified type

def coerce_type(value: Any, target_type: str) -> Any:
    """
    Attempts to convert a given value to a specified target type.

    Args:
        value (Any): The value to be converted.
        target_type (str): The desired target type (e.g., 'string', 'integer').

    Returns:
        Any: The value coerced to the target type, or the original value if conversion is not feasible.
    """
    # Convert to string
    if target_type == 'string':
        return str(value)
    # Convert to integer, handling float to integer conversion
    elif target_type == 'integer':
        return int(float(value))
    # Convert to float (for numbers)
    elif target_type == 'number':
        return float(value)
    # Convert to boolean
    elif target_type == 'boolean':
        return bool(value)
    # Ensure value is a list if target type is array
    elif target_type == 'array':
        return [value] if not isinstance(value, list) else value
    # Ensure value is a dictionary if target type is object
    elif target_type == 'object':
        return {} if not isinstance(value, dict) else value
    # If target type doesn't match, return the value as is
    else:
        return value
