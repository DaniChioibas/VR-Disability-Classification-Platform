import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from joblib import load
import os
import numpy as np
from .models import calculate_statistics

# Loading the models
model_path = os.path.join(os.path.dirname(__file__), 'classifier_model.joblib')
try:
    model = load(model_path)
except FileNotFoundError:
    model = None

extra_model_path = os.path.join(os.path.dirname(__file__), 'classifier_model_extra.pkl')
try:
    extra_model = load(extra_model_path)
except FileNotFoundError:
    extra_model = None

@csrf_exempt
def predict_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            raw_head_positions = []
            processed_positions = [] 
            
            for entry in data:
                try:
                    pos = entry['HeadPosition']
                    forw = entry['HeadForward']
                    
                    poz_ml = [float(pos['x']), float(pos['y']), float(pos['z'])]
                    forz_ml = [float(forw['x']), float(forw['y']), float(forw['z'])]
                    processed_positions.append(poz_ml + forz_ml)
                    
                    raw_head_positions.append({'x': float(pos['x']), 'y': float(pos['y']), 'z': float(pos['z'])})
                except (KeyError, ValueError) as e:
                    continue
            
            if not processed_positions:
                return JsonResponse({"error": "No valid position data found in the request for classification"}, status=400)
                
            if not raw_head_positions:
                return JsonResponse({"error": "No valid head position data found"}, status=400)

            processed_positions_np = np.array(processed_positions)
            features = calculate_statistics(processed_positions_np).reshape(1, -1)
            
            if model is None:
                return JsonResponse({"error": "Model not loaded. Please check the server configuration."}, status=500)
            
            prediction = model.predict(features)
            prediction_proba = model.predict_proba(features)[0]
            prediction_label = "Atypical" if prediction[0] == 1 else "Typical"
            
            confidence = prediction_proba[1] if prediction[0] == 1 else prediction_proba[0]
            confidence_percentage = round(confidence * 100, 1)
            return JsonResponse({
                "status": "success",
                "model_type": "standard",
                "prediction": int(prediction[0]),
                "prediction_label": prediction_label,
                "confidence": confidence_percentage
            })
                
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error processing request: {str(e)}"}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are accepted"}, status=405)

@csrf_exempt
def predict_extra_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            
            raw_head_positions = []
            processed_positions = [] 
            
            for entry in data:
                try:
                    pos = entry['HeadPosition']
                    forw = entry['HeadForward']
                    
                    poz_ml = [float(pos['x']), float(pos['y']), float(pos['z'])]
                    forz_ml = [float(forw['x']), float(forw['y']), float(forw['z'])]
                    processed_positions.append(poz_ml + forz_ml)
                    

                    raw_head_positions.append({'x': float(pos['x']), 'y': float(pos['y']), 'z': float(pos['z'])})
                except (KeyError, ValueError) as e:
                    continue
            
            if not processed_positions:
                return JsonResponse({"error": "No valid position data found in the request for classification"}, status=400)
                
            if not raw_head_positions:
                return JsonResponse({"error": "No valid head position data found"}, status=400)
            
            processed_positions_np = np.array(processed_positions)
            features = calculate_statistics(processed_positions_np).reshape(1, -1)
            
            if extra_model is None:
                return JsonResponse({"error": "Extra model not loaded. Please check the server configuration."}, status=500)
            
            prediction = extra_model.predict(features)
            prediction_proba = extra_model.predict_proba(features)[0]
            prediction_label = "Autism" if prediction[0] == 1 else "Non-Autism"
            
            confidence = prediction_proba[1] if prediction[0] == 1 else prediction_proba[0]
            confidence_percentage = round(confidence * 100, 1)
            
            return JsonResponse({
                "status": "success",
                "model_type": "extra",
                "prediction": int(prediction[0]),
                "prediction_label": prediction_label,
                "confidence": confidence_percentage
            })
                
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error processing request: {str(e)}"}, status=500)
    else:
        return JsonResponse({"error": "Only POST requests are accepted"}, status=405)
