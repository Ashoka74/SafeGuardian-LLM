
import streamlit as st
from google.generativeai.types import content_types
from collections.abc import Iterable
import time
from sodapy import Socrata
import json
from IPython.display import display
from IPython.display import Markdown
# import ABC and abstract
from abc import ABC, abstractmethod
from enum import Enum
import pathlib
import textwrap
import google.generativeai as genai
from IPython.display import display
from IPython.display import Markdown
from typing import List, Tuple, Optional, Dict, Any

from victim_tools.llm_utils import GeminiConfig


gemini_api = 'AIzaSyAEALAXiaE1HcD8qcN1duY4OtmUDfYqquk'
model_path = 'models/gemini-1.5-flash'
response_type = 'application/json'

class SupportType(Enum):
    PSYCHOLOGICAL = 'psychological'
    PHYSICAL = 'physical'
    EMOTIONAL = 'emotional'

class DisasterType(Enum):
    EARTHQUAKE = 'earthquake'
    WILDFIRE = 'wildfire'
    FLOOD = 'flood'
    TSUNAMI = 'tsunami'
    BOMB = 'bomb'

class InformType(Enum):
    ROAD_BLOCKS = 'road_blocks'
    FRIENDS_STATUS = 'friend_status'
    HELP_STATUS = 'help_status'
    QUEUE_POSITION = 'queue_pos'


def to_markdown(text):
  text = text.replace('•', '  *')
  return Markdown(textwrap.indent(text, '> ', predicate=lambda _: True))
