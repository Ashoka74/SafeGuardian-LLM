import requests
import json

import pandas as pd 
dataset_coordinates = pd.read_csv('datasets/health_check_descriptions.csv')
dataset_coordinates.dropna(subset=['risk_nb', 'latitude'])

rescue_centers_coordinate = pd.read_csv('datasets/sf_rescue_dep.csv')

def emergency_to_weight(emergency_level, base_penalty=3600, max_penalty=7200):
    """
    Convert emergency level to a weight in seconds.
    
    :param emergency_level: Integer from 1 to 5, where 5 is most urgent
    :param base_penalty: Base penalty in seconds (default 1 hour)
    :param max_penalty: Maximum penalty in seconds (default 2 hours)
    :return: Weight in seconds
    """
    if emergency_level < 1 or emergency_level > 5:
        raise ValueError("Emergency level must be between 1 and 5")
    
    # Invert the emergency level so that higher emergencies get lower weights
    inverted_level = 6 - emergency_level
    
    # Calculate weight: lower emergency levels get higher penalties
    weight = base_penalty + (inverted_level - 1) * (max_penalty - base_penalty) / 4
    
    return int(weight)


def get_osrm_trip(coordinates, weights=None, api_url="http://router.project-osrm.org/trip/v1/driving/", rescue_center=None):
    """
    Make a request to the OSRM Trip API and return the GeoJSON response.
    
    :param coordinates: List of coordinate pairs [longitude, latitude]
    :param weights: List of weights (in seconds) corresponding to each coordinate
    :param api_url: Base URL for the OSRM API
    :return: GeoJSON object of the route
    """
    if rescue_center:
        coordinates.insert(0, rescue_center)
        weights.insert(0, 0) if weights else None


    if weights and len(weights) != len(coordinates):
        raise ValueError("The number of weights must match the number of coordinates")

    # Convert coordinates to string format required by OSRM
    if weights:
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
        weights_str = ";".join([str(w) for w in weights])
        url = f"{api_url}{coords_str}?geometries=geojson&overview=full&durations={weights_str}"
    else:
        coords_str = ";".join([f"{lon},{lat}" for lon, lat in coordinates])
        url = f"{api_url}{coords_str}?roundtrip=true&source=first&destination=any&geometries=geojson&overview=full"
    
    # Make the API request
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        
        # Extract the GeoJSON from the response
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



# Example usage
if __name__ == "__main__":
   
    rescue_coords = rescue_centers_coordinate[['longitude', 'latitude']].values.tolist()[0]
    # Example emergency levels (1-5, where 5 is most urgent)
    emergency_levels = dataset_coordinates['risk_nb'].values.tolist()
    coordinates = dataset_coordinates[['longitude', 'latitude']].values.tolist()
    coordinates.insert(0, rescue_coords)
    weights = [emergency_to_weight(level) for level in emergency_levels]
    weights.insert(0, 0)  # No penalty for the rescue center
    result = get_osrm_trip(coordinates, weights)
    
    if result:
        print(json.dumps(result, indent=2))
        
        # Optionally, save the GeoJSON to a file
        with open("trip_route_weighted.geojson", "w") as f:
            json.dump(result, f)
        print("GeoJSON saved to 'trip_route_weighted.geosjon'")
    else:
        print("Failed to get the route.")

    # Compare with unweighted route
    unweighted_result = get_osrm_trip(coordinates)
    if unweighted_result:
        print("\nUnweighted route:")
        print(json.dumps(unweighted_result, indent=2))
        
        with open("trip_route_unweighted.geojson", "w") as f:
            json.dump(unweighted_result, f)
        print("Unweighted GeoJSON saved to 'trip_route_unweighted.geojson'")
    else:
        print("Failed to get the unweighted route.")