import requests
import json
import sys

def test_api(url="http://localhost:8000/api/predict/", data_file=None):
    """
    Test the VR Data Classifier API by sending a POST request with example data
    
    Args:
        url (str): The API endpoint URL
        data_file (str): Path to a JSON file containing test data
    
    Returns:
        dict: The API response
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    if data_file:
        try:
            with open(data_file, 'r') as f:
                data = json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Error loading data file: {e}")
            return None
    else:
        data = [
            {
                "HeadPosition": {
                    "x": 0.76394,
                    "y": 2.91133,
                    "z": 0.04299
                },
                "HeadForward": {
                    "x": -0.75834,
                    "y": -0.41199,
                    "z": 0.50514
                }
            },
            {
                "HeadPosition": {
                    "x": 0.76894,
                    "y": 2.92133,
                    "z": 0.04399
                },
                "HeadForward": {
                    "x": -0.75834,
                    "y": -0.41199,
                    "z": 0.50514
                }
            }
        ]
    
    try:
        print(f"Sending request to {url}...")
        response = requests.post(url, data=json.dumps(data), headers=headers)
        
        print(f"Status Code: {response.status_code}")
        response_data = response.json()
        print(f"Response: {json.dumps(response_data, indent=4)}")
        
        return response_data
    except requests.RequestException as e:
        print(f"Error making request: {e}")
        return None

if __name__ == "__main__":
    data_file = sys.argv[1] if len(sys.argv) > 1 else None
    test_api(data_file=data_file)
