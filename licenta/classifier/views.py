import json
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
import numpy as np
from joblib import load
import os
from .models import calculate_statistics, ClassificationHistory, PatientSession
from django.conf import settings
from django.http import Http404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout 
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .forms import PatientSessionForm

model_path = os.path.join(os.path.dirname(__file__), 'classifier_model.joblib')
try:
    model = load(model_path)
except FileNotFoundError:
    model = None

model_extra_path = os.path.join(os.path.dirname(__file__), 'classifier_model_extra.pkl')
try:
    model_extra = load(model_extra_path)
except FileNotFoundError:
    print("Error: model_extra.pkl not found.")
    model_extra = None
except Exception as e:
    print(f"Error loading model_extra.pkl: {e}")
    model_extra = None

def documentation_view(request):
    return render(request, 'classifier/documentation.html')

def advanced_classification_view(request):
    classification_data = request.session.get('classification_data', None)
    
    if classification_data and classification_data.get('prediction') == 1:
        advanced_results = {
            'movement_type': 'Repetitive',
            'severity_score': 0.75,
            'pattern_details': {
                'repetition_frequency': '5.2 Hz',
                'amplitude_variance': 'High',
                'directional_bias': 'Lateral',
            },
            'recommendations': [
                'Consider detailed analysis of lateral movement patterns',
                'Examine head tilt frequency and duration',
                'Analyze acceleration peaks during movement transitions'
            ]
        }
        
        classification_data['advanced_results'] = advanced_results
        request.session['classification_data'] = classification_data
        
        return render(request, 'classifier/advanced_analysis.html', {
            'classification_data': classification_data,
            'advanced_results': advanced_results
        })
    else:
        return redirect('explore_more') 

def classifier_view(request):
    if request.method == "POST":
        json_file = request.FILES.get("json_file")
        if json_file:
            try:
                json_file_content = json_file.read()
                data = json.loads(json_file_content)
                
                processed_positions = [] 
                for entry in data:
                    try:
                        pos = entry['HeadPosition']
                        forw = entry['HeadForward']
                        
                        poz_ml = [float(pos['x']), float(pos['y']), float(pos['z'])]
                        forz_ml = [float(forw['x']), float(forw['y']), float(forw['z'])]
                        processed_positions.append(poz_ml + forz_ml)
                        
                    except (KeyError, ValueError) as e:
                        continue 
                
                if not processed_positions:
                    return JsonResponse({"error": "No valid position data found in the file for classification"}, status=400)
                
                processed_positions_np = np.array(processed_positions)
                features = calculate_statistics(processed_positions_np).reshape(1, -1)
                
                if model is None:
                    return JsonResponse({"error": "Model not loaded. Please train the model first."}, status=500)
                
                prediction = model.predict(features)
                prediction_proba = model.predict_proba(features)[0]
                prediction_label = "Atypical" if prediction[0] == 1 else "Typical"
                
                confidence = prediction_proba[1] if prediction[0] == 1 else prediction_proba[0]
                confidence_percentage = round(confidence * 100, 1)

                request.session['uploaded_json_data'] = json_file_content.decode('utf-8') 

                classification_data_for_session = {
                    "prediction": int(prediction[0]), 
                    "prediction_label": prediction_label,
                    "confidence": confidence_percentage,
                    "filename": json_file.name 
                }

                if prediction_label == "Atypical":
                    classification_data_for_session["features"] = features.tolist()
                
                request.session['classification_data'] = classification_data_for_session
                
                if request.user.is_authenticated:
                    ClassificationHistory.objects.create(
                        user=request.user,
                        filename=json_file.name,
                        prediction_label=prediction_label,
                        confidence=confidence_percentage,
                        raw_json=json_file_content.decode('utf-8')
                    )

                return JsonResponse({
                    "message": "Classification completed",
                    "prediction": int(prediction[0]),
                    "prediction_label": prediction_label,
                    "confidence": confidence_percentage
                })
            except json.JSONDecodeError:
                return JsonResponse({"error": "Invalid JSON file"}, status=400)
            except Exception as e:
                print(f"Error in classifier_view: {str(e)}")
                import traceback
                traceback.print_exc()
                return JsonResponse({"error": f"Error processing file: {str(e)}"}, status=500)
        else:
            return JsonResponse({"error": "No file uploaded"}, status=400)
            
    return render(request, 'classifier/index.html')

def batch_analysis_view(request):
    context = {
        'results': [],
        'form_errors': None
    }
    if request.method == "POST":
        json_files = request.FILES.getlist("json_files_batch")
        
        if not json_files:
            context['form_errors'] = "No files were uploaded."
            return render(request, 'classifier/batch_upload.html', context)

        for json_file in json_files:
            file_result = {"filename": json_file.name}
            try:
                json_file_content = json_file.read()
                data = json.loads(json_file_content)
                
                processed_positions = []
                for entry in data:
                    try:
                        pos = entry['HeadPosition']
                        forw = entry['HeadForward']
                        poz_ml = [float(pos['x']), float(pos['y']), float(pos['z'])]
                        forz_ml = [float(forw['x']), float(forw['y']), float(forw['z'])]
                        processed_positions.append(poz_ml + forz_ml)
                    except (KeyError, ValueError):
                        continue
                
                if not processed_positions:
                    file_result["error"] = "No valid position data found in the file."
                    context['results'].append(file_result)
                    continue
                
                processed_positions_np = np.array(processed_positions)
                features = calculate_statistics(processed_positions_np).reshape(1, -1)
                
                if model is None:
                    file_result["error"] = "Main model not loaded."
                    context['results'].append(file_result)
                    continue
                
                prediction = model.predict(features)
                prediction_proba = model.predict_proba(features)[0]
                prediction_label = "Atypical" if prediction[0] == 1 else "Typical"
                confidence = prediction_proba[1] if prediction[0] == 1 else prediction_proba[0]
                confidence_percentage = round(confidence * 100, 1)

                file_result.update({
                    "prediction_label": prediction_label,
                    "confidence": confidence_percentage,
                    "prediction": int(prediction[0]),
                })

                if request.user.is_authenticated:
                    ClassificationHistory.objects.create(
                        user=request.user,
                        filename=json_file.name,
                        prediction_label=prediction_label,
                        confidence=confidence_percentage,
                        raw_json=json_file_content.decode('utf-8')
                    )

                if prediction_label == "Atypical":
                    file_result["features_json"] = json.dumps(features.tolist()) 
                    file_result["raw_json_content_json"] = json.dumps(json.loads(json_file_content.decode('utf-8'))) 

            except json.JSONDecodeError:
                file_result["error"] = "Invalid JSON format."
            except Exception as e:
                print(f"Error processing file {json_file.name} in batch_analysis_view: {str(e)}")
                file_result["error"] = f"Error processing file: {str(e)}"
            context['results'].append(file_result)
            
    return render(request, 'classifier/batch_upload.html', context)

def set_explore_session_api(request):
    if request.method == "POST":
        try:
            features_json_str = request.POST.get('features')
            raw_json_content_json_str = request.POST.get('raw_json_content')
            filename = request.POST.get('filename')
            prediction_label = request.POST.get('prediction_label')
            confidence_str = request.POST.get('confidence')

            if not all([features_json_str, raw_json_content_json_str, filename, prediction_label, confidence_str]):
                return JsonResponse({"error": "Missing data for explore session."}, status=400)

            request.session['uploaded_json_data'] = raw_json_content_json_str 
            request.session['classification_data'] = {
                "prediction": 1 if prediction_label == "Atypical" else 0,
                "prediction_label": prediction_label,
                "confidence": float(confidence_str),
                "features": json.loads(features_json_str),
                "filename": filename
            }
            
            return JsonResponse({"status": "success", "message": "Explore session data set."})
        except json.JSONDecodeError as je:
            print(f"JSONDecodeError in set_explore_session_api: {je}")
            return JsonResponse({"error": "Invalid JSON data in request for explore session."}, status=400)
        except Exception as e:
            print(f"Error in set_explore_session_api: {str(e)}")
            return JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
    return JsonResponse({"error": "Invalid request method. Use POST."}, status=405)

def explore_more_view(request):
    json_data_str_from_session = request.session.get('uploaded_json_data', None) 
    initial_classification_data = request.session.get('classification_data', None)

    pretty_json_data = None
    data_stats = None
    axis_stats = {}
    if json_data_str_from_session:
        try:
            data_to_dump = json.loads(json_data_str_from_session)
            pretty_json_data = json.dumps(data_to_dump, indent=4)
            from datetime import datetime
            import numpy as np
            if isinstance(data_to_dump, list) and data_to_dump:
                first_dt = None
                for entry in data_to_dump:
                    dt = entry.get('dateTime')
                    if dt:
                        first_dt = dt
                        break
                last_dt = None
                for entry in reversed(data_to_dump):
                    dt = entry.get('dateTime')
                    if dt:
                        last_dt = dt
                        break
                first_dt = first_dt or 'N/A'
                last_dt = last_dt or 'N/A'
                try:
                    start = datetime.fromisoformat(first_dt.rstrip('Z')) if first_dt != 'N/A' else None
                    end = datetime.fromisoformat(last_dt.rstrip('Z')) if last_dt != 'N/A' else None
                    duration = end - start
                except Exception:
                    duration = None
                data_stats = {
                    'first_recorded': first_dt,
                    'last_recorded': last_dt,
                    'sample_count': len(data_to_dump),
                    'duration': str(duration) if duration is not None else 'N/A'
                }
                hp_axes = {'x': [], 'y': [], 'z': []}
                hf_axes = {'x': [], 'y': [], 'z': []}
                for entry in data_to_dump:
                    pos = entry.get('HeadPosition', {})
                    fwd = entry.get('HeadForward', {})
                    for a in ['x','y','z']:
                        try:
                            hp_axes[a].append(float(pos.get(a, 0)))
                            hf_axes[a].append(float(fwd.get(a, 0)))
                        except ValueError:
                            continue
                for key, axes in [('HeadPosition', hp_axes), ('HeadForward', hf_axes)]:
                    stats = {}
                    for a, vals in axes.items():
                        if vals:
                            arr = np.array(vals)
                            stats[a] = {
                                'mean': float(arr.mean()),
                                'std': float(arr.std()),
                                'min': float(arr.min()),
                                'max': float(arr.max())
                            }
                        else:
                            stats[a] = {'mean': None, 'std': None, 'min': None, 'max': None}
                    axis_stats[key] = stats
        except json.JSONDecodeError:
            pretty_json_data = "Error: Could not decode JSON data from session."
        except TypeError: 
             pretty_json_data = "Error: Invalid type for JSON data in session."

    context = {
        'json_data': pretty_json_data,
        'prediction_label': None,
        'confidence': None,
        'filename': None, 
        'secondary_prediction_label': None,
        'secondary_confidence': None,
        'show_secondary_classify_button': False,
        'secondary_classification_error': None,
        'axis_stats': axis_stats
    }
    if json_data_str_from_session:
        context['raw_json_list'] = json_data_str_from_session
    if data_stats:
        context['data_stats'] = data_stats

    if initial_classification_data:
        context['prediction_label'] = initial_classification_data.get('prediction_label')
        context['confidence'] = initial_classification_data.get('confidence')
        context['filename'] = initial_classification_data.get('filename') 
        if context['prediction_label'] == "Atypical":
             context['show_secondary_classify_button'] = True
    
    if request.method == "POST":
        context['show_secondary_classify_button'] = False 

        if model_extra is None:
            context['secondary_classification_error'] = "Secondary classification model (model_extra.pkl) is not loaded."
        elif not initial_classification_data or initial_classification_data.get('prediction_label') != "Atypical":
            context['secondary_classification_error'] = "Secondary classification is only available for 'Atypical' initial results."
        else:
            features_list = initial_classification_data.get('features')
            if features_list:
                try:
                    features_np = np.array(features_list).reshape(1, -1) 
                    
                    secondary_prediction = model_extra.predict(features_np)
                    secondary_prediction_proba = model_extra.predict_proba(features_np)[0]
                    
                    sec_pred_label = "Autism" if secondary_prediction[0] == 1 else "Non-autism disability"
                    sec_confidence = secondary_prediction_proba[1] if secondary_prediction[0] == 1 else secondary_prediction_proba[0]
                    sec_confidence_percentage = round(sec_confidence * 100, 1)

                    context['secondary_prediction_label'] = sec_pred_label
                    context['secondary_confidence'] = sec_confidence_percentage
                except AttributeError as ae:
                    print(f"AttributeError during secondary classification: {ae}.")
                    context['secondary_classification_error'] = f"Model error during secondary classification. ({ae})"
                except Exception as e:
                    print(f"Error during secondary classification: {str(e)}")
                    context['secondary_classification_error'] = f"An unexpected error occurred: {str(e)}"
            else:
                context['secondary_classification_error'] = "Features for secondary classification not found."
    
    if context['secondary_prediction_label']: 
        context['show_secondary_classify_button'] = False

    return render(request, 'classifier/explore_more.html', context)

def download_script_view(request):
    script_path = os.path.join(settings.BASE_DIR, 'script', 'script.rar')
    if os.path.exists(script_path):
        with open(script_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/vnd.rar")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(script_path)
            return response
    else:
        return HttpResponse("No script available for download.", content_type="text/plain")

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = UserCreationForm()
    return render(request, 'classifier/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('index')

@require_POST
def batch_explore_view(request):
    features_json_str = request.POST.get('features')
    raw_json_content_json_str = request.POST.get('raw_json_content')
    filename = request.POST.get('filename')
    prediction_label = request.POST.get('prediction_label')
    confidence_str = request.POST.get('confidence')

    if not all([features_json_str, raw_json_content_json_str, filename, prediction_label, confidence_str]):
        return redirect('batch_analysis')

    # Store in session
    request.session['uploaded_json_data'] = raw_json_content_json_str
    request.session['classification_data'] = {
        "prediction": 1 if prediction_label == "Atypical" else 0,
        "prediction_label": prediction_label,
        "confidence": float(confidence_str),
        "features": json.loads(features_json_str),
        "filename": filename
    }
    return redirect('explore_more')

@login_required
def dashboard_view(request):
    """Dashboard listing patient's sessions and recent classifications"""
    sessions = PatientSession.objects.filter(user=request.user)
    history = ClassificationHistory.objects.filter(user=request.user) 
    return render(request, 'classifier/dashboard.html', {
        'sessions': sessions,
        'history': history
    })

@login_required
def session_create_view(request):
    if request.method == 'POST':
        form = PatientSessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.user = request.user
            session.save()
            return redirect('session_detail', session_id=session.id)
    else:
        form = PatientSessionForm()
    return render(request, 'classifier/session_form.html', {'form': form})

@login_required
def session_detail_view(request, session_id):
    session = get_object_or_404(PatientSession, pk=session_id, user=request.user)
    history = ClassificationHistory.objects.filter(session=session)
    result = None
    error = None
    if request.method == 'POST':
        json_file = request.FILES.get('json_file')
        if json_file:
            try:
                data = json.load(json_file)
                processed = []
                for entry in data:
                    try:
                        pos = entry['HeadPosition']; forw = entry['HeadForward']
                        processed.append([float(pos['x']), float(pos['y']), float(pos['z'])] +
                                         [float(forw['x']), float(forw['y']), float(forw['z'])])
                    except: continue
                if not processed:
                    raise ValueError('No valid data')
                features = calculate_statistics(np.array(processed)).reshape(1,-1)
                pred = model.predict(features)[0]
                label = 'Atypical' if pred==1 else 'Typical'
                proba = model.predict_proba(features)[0][pred]
                confidence = round(proba*100,1)
                ClassificationHistory.objects.create(
                    user=request.user,
                    session=session,
                    filename=json_file.name,
                    prediction_label=label,
                    confidence=confidence,
                    raw_json=json.dumps(data)
                )
                result = {'label': label, 'confidence': confidence}
            except Exception as e:
                error = str(e)
        else:
            error = 'No file uploaded.'
    return render(request, 'classifier/session_detail.html', {
        'session': session,
        'history': history,
        'result': result,
        'error': error
    })

@login_required
@require_POST
def session_delete_view(request, session_id):
    session = get_object_or_404(PatientSession, pk=session_id, user=request.user)
    session.delete()
    return redirect('dashboard')

@login_required
def history_explore_view(request, history_id):
     record = get_object_or_404(ClassificationHistory, pk=history_id, user=request.user)
     request.session['uploaded_json_data'] = record.raw_json
     classification_data = {
         'prediction': 1 if record.prediction_label == 'Atypical' else 0,
         'prediction_label': record.prediction_label,
         'confidence': record.confidence,
         'filename': record.filename
     }
     if record.prediction_label == 'Atypical':
         try:
             data_list = json.loads(record.raw_json)
             processed_positions = []
             for entry in data_list:
                 try:
                     pos = entry['HeadPosition']; forw = entry['HeadForward']
                     processed_positions.append([
                         float(pos['x']), float(pos['y']), float(pos['z']),
                         float(forw['x']), float(forw['y']), float(forw['z'])
                     ])
                 except (KeyError, ValueError):
                     continue
             if processed_positions:
                 features_np = calculate_statistics(np.array(processed_positions)).reshape(1, -1)
                 classification_data['features'] = features_np.tolist()
         except Exception:
             pass
     request.session['classification_data'] = classification_data
     return redirect('explore_more')