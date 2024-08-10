# config.py

import os
import configparser
from typing import Dict, Any

class GeminiConfig:
    def __init__(self, gemini_api: str, model_path: str, response_type: str, geolocator_api: str, safety_settings: Dict[str, Any]):
        self.gemini_api = gemini_api
        self.model_path = model_path
        self.response_type = response_type
        self.geolocator_api = geolocator_api
        self.safety_settings = safety_settings

    @classmethod
    def from_file(cls, config_file: str):
        config = configparser.ConfigParser()
        config.read(config_file)

        gemini_api = config.get('API', 'gemini_api', fallback=os.getenv('GEMINI_API'))
        model_path = config.get('MODEL', 'model_path', fallback='models/gemini-1.5-flash')
        response_type = config.get('MODEL', 'response_type', fallback='application/json')
        geolocator_api = config.get('API', 'geolocator_api', fallback=os.getenv('GEOLOCATOR_API'))
        
        safety_settings = {
            'harassment': config.getfloat('SAFETY', 'harassment', fallback=0.1),
            'hate_speech': config.getfloat('SAFETY', 'hate_speech', fallback=0.1),
            'sexually_explicit': config.getfloat('SAFETY', 'sexually_explicit', fallback=0.1),
            'dangerous_content': config.getfloat('SAFETY', 'dangerous_content', fallback=0.1)
        }

        return cls(gemini_api, model_path, response_type, geolocator_api, safety_settings)