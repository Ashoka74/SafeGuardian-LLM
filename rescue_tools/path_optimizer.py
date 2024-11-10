"""
OSRM Path Optimizer for Emergency Response Routing
===============================================

This module provides emergency response route optimization using the OSRM (Open Source Routing Machine) API.
It specializes in calculating optimal routes while considering emergency priority levels and rescue center locations.

Key Features:
    - Emergency level weighting system
    - Integration with OSRM Trip API
    - Support for rescue center-based routing
    - GeoJSON route generation
    - Priority-based path optimization

Dependencies:
    - requests: For API communication
    - pandas: For data handling
    - json: For GeoJSON processing

Author: Sinan 
Modified by: Andrew 
Version: 1.0.0
"""

import requests
import json
import pandas as pd

def emergency_to_weight(emergency_level: int, base_penalty: int = 3600, 
                       max_penalty: int = 7200) -> int:
    """
    Converts emergency severity levels to routing weights for path optimization.
    
    Higher emergency levels result in lower weights, prioritizing faster response times.
    Weight calculation uses linear interpolation between base and max penalties.
    
    Args:
        emergency_level (int): Severity level from 1 (most severe) to 5 (least severe)
        base_penalty (int, optional): Minimum penalty in seconds. Defaults to 3600 (1 hour)
        max_penalty (int, optional): Maximum penalty in seconds. Defaults to 7200 (2 hours)
    
    Returns:
        int: Calculated weight in seconds
    
    Raises:
        ValueError: If emergency_level is not between 1 and 5
    
    Examples:
        >>> emergency_to_weight(1)  # Most severe
        3600  # Base penalty
        >>> emergency_to_weight(5)  # Least severe
        7200  # Max penalty
    """
    if emergency_level < 1 or emergency_level > 5:
        raise ValueError("Emergency level must be between 1 and 5")
    
    inverted_level = 6 - emergency_level
    weight = base_penalty + (inverted_level - 1) * (max_penalty - base_penalty) / 4
    
    return int(weight)

def get_osrm_trip(coordinates: list, weights: list = None, 
                  api_url: str = "http://router.project-osrm.org/trip/v1/driving/",
                  rescue_center: list = None) -> dict:
    """
    Generates optimized route using OSRM Trip API with support for weighted locations
    and rescue center integration.
    
    Args:
        coordinates (list): List of [longitude, latitude] pairs for each location
        weights (list, optional): List of time penalties in seconds for each location
        api_url (str, optional): OSRM API endpoint URL
        rescue_center (list, optional): [longitude, latitude] of rescue center
    
    Returns:
        dict: GeoJSON object containing:
            - type: "FeatureCollection"
            - features: List containing route geometry and properties
                - geometry: Route line geometry
                - properties:
                    - distance: Total route distance
                    - duration: Total route duration
                    - waypoints: Order of visited locations
    
    Raises:
        ValueError: If weights length doesn't match coordinates length
        RequestException: If OSRM API request fails
    
    Example:
        >>> coords = [[2.3, 48.9], [2.4, 48.8]]  # Paris coordinates
        >>> weights = [3600, 7200]  # Time penalties
        >>> route = get_osrm_trip(coords, weights)
        >>> print(route['features'][0]['properties']['distance'])
        12345.67  # Distance in meters
    
    Notes:
        - OSRM API response includes detailed trip information
        - Rescue center is always first and last point if provided
        - Weights affect route optimization but not actual travel times
        - Uses 'geojson' geometry format for compatibility with mapping libraries
    """
    if rescue_center:
        coordinates.insert(0, rescue_center)
        if weights:
            weights.insert(0, 0)

    if weights and len(weights) != len(coordinates):
        raise ValueError("The number of weights must match the number of coordinates")

    # Format coordinates for OSRM API
    coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
    
    # Build API URL with appropriate parameters
    if weights:
        weights_str = ";".join([str(w) for w in weights])
        url = f"{api_url}{coords_str}?geometries=geojson&overview=full&durations={weights_str}"
    else:
        url = (f"{api_url}{coords_str}?roundtrip=true&source=first&"
               "destination=any&geometries=geojson&overview=full")
    
    # Execute API request
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        # Construct GeoJSON response
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": data["trips"][0]["geometry"],
                    "properties": {
                        "distance": data["trips"][0]["distance"],
                        "duration": data["trips"][0]["duration"],
                        "waypoints": data["waypoints"]
                    }
                }
            ]
        }
        
        return geojson
    else:
        print(f"Error: API request failed with status code {response.status_code}")
        return None

if __name__ == "__main__":
    """
    Example usage of path optimizer with sample data.
    
    Demonstrates:
        1. Loading rescue center and emergency location data
        2. Converting emergency levels to weights
        3. Generating optimized routes
        4. Saving results as GeoJSON files
    """
    # Load sample data
    rescue_centers_coordinate = pd.read_csv('datasets/sf_rescue_dep.csv')
    dataset_coordinates = pd.read_csv('datasets/health_check_descriptions.csv')
    dataset_coordinates.dropna(subset=['risk_nb', 'latitude'])
    
    # Extract rescue center coordinates
    rescue_coords = rescue_centers_coordinate[['longitude', 'latitude']].values.tolist()[0]
    
    # Prepare emergency data
    emergency_levels = dataset_coordinates['risk_nb'].values.tolist()
    coordinates = dataset_coordinates[['longitude', 'latitude']].values.tolist()
    coordinates.insert(0, rescue_coords)
    
    # Calculate weights from emergency levels
    weights = [emergency_to_weight(level) for level in emergency_levels]
    weights.insert(0, 0)  # No penalty for rescue center
    
    # Generate and save weighted route
    result = get_osrm_trip(coordinates, weights)
    if result:
        print(json.dumps(result, indent=2))
        with open("trip_route_weighted.geojson", "w") as f:
            json.dump(result, f)
        print("GeoJSON saved to 'trip_route_weighted.geojson'")
    
    # Generate and save unweighted route for comparison
    unweighted_result = get_osrm_trip(coordinates)
    if unweighted_result:
        print("\nUnweighted route:")
        print(json.dumps(unweighted_result, indent=2))
        with open("trip_route_unweighted.geojson", "w") as f:
            json.dump(unweighted_result, f)
        print("Unweighted GeoJSON saved to 'trip_route_unweighted.geojson'")
