import requests
import json

with open('sample_data.json', 'r') as f:
    sample_data = json.load(f)


def test_extra_api():
    print("\nTesting extra API endpoint...")
    url = "http://localhost:8000/api/predict-extra/"
    
    try:
        response = requests.post(url, json=sample_data, headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            result = response.json()
            print("Extra API Response:")
            print(f"  Status: {result.get('status')}")
            print(f"  Model Type: {result.get('model_type')}")
            print(f"  Prediction: {result.get('prediction')} ({result.get('prediction_label')})")
            print(f"  Confidence: {result.get('confidence')}%")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure it's running.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_extra_api()
