from django.db import models
import os
import json
import numpy as np
from glob import glob
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from joblib import dump
from django.contrib.auth.models import User
from django.utils import timezone


def read_json_files_with_labels(directory, label):
    player_positions = []
    labels = []
    
    for filepath in glob(os.path.join(directory, '*.json')):
        positions = []
        forwards = []
        with open(filepath, 'r') as file:
            data = json.load(file)
            for entry in data:
                try:
                    pos = entry['HeadPosition']
                    forw = entry['HeadForward']
                    poz=[float(pos['x']), float(pos['y']), float(pos['z'])]
                    forz=[float(forw['x']), float(forw['y']), float(forw['z'])]
                    positions.append(poz+forz)
                except KeyError:
                    continue
                except ValueError:
                    continue
        if positions:
            player_positions.append(np.array(positions))
            labels.append(label)
    
    return player_positions, labels
    
def calculate_statistics(positions):
    mean_positions = np.mean(positions, axis=0)
    var_positions = np.var(positions, axis=0)
    return np.hstack([mean_positions, var_positions])

def train_model():
    tipici_directory = os.path.join('classifier_data', 'FullData', 'tipici')
    atipici_directory = os.path.join('classifier_data', 'FullData', 'atipici')

    tipici_positions, tipici_labels = read_json_files_with_labels(tipici_directory, 0)
    atipici_positions, atipici_labels = read_json_files_with_labels(atipici_directory, 1)

    player_positions = tipici_positions + atipici_positions
    labels = tipici_labels + atipici_labels

    features = np.array([calculate_statistics(positions) for positions in player_positions])
    labels = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

    model = RandomForestClassifier(random_state=42)

    model.fit(X_train, y_train)

    dump(model, 'classifier_model.joblib')

    return model

class PatientSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.name} ({self.created_at.strftime('%Y-%m-%d')})"

class ClassificationHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(PatientSession, null=True, blank=True, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)
    filename = models.CharField(max_length=255, blank=True)
    prediction_label = models.CharField(max_length=50)
    confidence = models.FloatField()
    raw_json = models.TextField(blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.prediction_label} on {self.timestamp}"
