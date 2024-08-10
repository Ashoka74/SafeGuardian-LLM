from typing import List, Tuple, Optional, Dict, Any
import time
from sodapy import Socrata

def get_rescue_data(incident_number: Optional[int] = "05083704", time: Optional[str] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())) -> List[Dict[str, Any]]:
    """
    Fetches rescue data for a specific incident number and time.

    Parameters:
    incident_number (Optional[str]): The incident number to fetch data for, if not provided, 05083704 will be used
    time (Optional[str]): The time to fetch data for. If not provided, the current time is used.

    Returns:
    str: A markdown formatted string with the rescue data.

    """
    if time is None:
        time = time.time()

    client = Socrata("data.sfgov.org", None)
    results = client.get("wr8u-xric", where="incident_number='{}'".format(incident_number))
    results = [{k: v for k, v in result.items() if k in ['arrival_dttm', 'first_unit_on_scene', 'point']} for result in results]
    str_res = f"Rescue data for incident number {incident_number} at time {time}:\n\n Arrival Time: {results[0]['arrival_dttm']}\n\n  First Unit On Scene: {results[0]['first_unit_on_scene']}\n\n  Location: {results[0]['point']['coordinates']}"
    return str_res
