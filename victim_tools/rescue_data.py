#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script: rescue_data.py
Description: Fetches rescue data for a specific incident number from San Francisco's open data portal.
Author: LangGang
"""

from typing import List, Tuple, Optional, Dict, Any  # Importing necessary types for type hinting
import time  # Importing time module to handle date and time formatting
from sodapy import Socrata  # Importing Socrata library to connect to Open Data APIs

def get_rescue_data(
    incident_number: Optional[int] = "05083704",  # Default incident number if none is provided
    time: Optional[str] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())  # Default current time in YYYY-MM-DD HH:MM:SS format
) -> List[Dict[str, Any]]:
    """
    Fetches rescue data for a specific incident number and time.

    Parameters:
    incident_number (Optional[str]): The incident number to fetch data for. 
                                     If not provided, defaults to "05083704".
    time (Optional[str]): The time for which data is fetched. 
                          Defaults to the current time if not provided.

    Returns:
    str: A markdown-formatted string with the rescue data.
    """
    if time is None:
        # If no time is provided, use the current timestamp
        time = time.time()

    # Initialize a Socrata client to connect to the San Francisco government data portal
    client = Socrata("data.sfgov.org", None)
    
    # Fetch rescue data where the incident number matches the specified incident_number
    results = client.get("wr8u-xric", where="incident_number='{}'".format(incident_number))
    
    # Filter each result to keep only specific fields: arrival time, first unit on scene, and location point
    results = [
        {k: v for k, v in result.items() if k in ['arrival_dttm', 'first_unit_on_scene', 'point']}
        for result in results
    ]

    # Format the rescue data into a readable string
    str_res = f"Rescue data for incident number {incident_number} at time {time}:\n\n"
    str_res += f"Arrival Time: {results[0]['arrival_dttm']}\n\n"  # Arrival time of rescue unit
    str_res += f"First Unit On Scene: {results[0]['first_unit_on_scene']}\n\n"  # First unit arrival time
    str_res += f"Location: {results[0]['point']['coordinates']}"  # Location coordinates

    return str_res  # Return the formatted string containing rescue details
