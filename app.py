from flask import Flask, request, render_template_string, url_for
import os
import uuid
import random
import json
from pydub import AudioSegment
import speech_recognition as sr
import librosa
import numpy as np
import joblib
from metadata_extractor import get_device_location, spoof_caller_location

app = Flask(__name__)

# Constants
EMERGENCY_KEYWORDS = [
    # General distress
    "help", "emergency", "urgent", "it's an emergency", "i need help", "i need assistance", 
    "call 911", "call the police", "call for help", "please help", "send help",

    # Medical emergencies
    "heart attack", "stroke", "unconscious", "not breathing", "can't breathe", 
    "bleeding", "choking", "seizure", "diabetic attack", "fainted", "collapsed",
    "allergic reaction", "overdose", "injury", "broken bone", "burns",

    # Fire-related
    "fire", "smoke", "house on fire", "forest fire", "burning", "flames", "explosion",

    # Crime-related
    "robbery", "burglary", "break in", "theft", "stolen", "assault", "attack",
    "murder", "shooting", "gunshots", "shots fired", "gun", "knife", "armed",
    "hostage", "kidnapped", "abduction", "rape", "sexual assault", "violence",

    # Domestic violence
    "domestic violence", "he hit me", "she hit me", "abuse", "being hurt", 
    "i'm in danger", "they're hurting me", "my partner is violent", "help me escape",

    # Vehicle/accidents
    "car crash", "accident", "hit and run", "collision", "ran over", "injured in crash", 
    "motorcycle accident", "truck crash", "vehicle fire",

    # Natural disasters
    "earthquake", "flood", "tornado", "hurricane", "tsunami", "landslide", 
    "storm", "wildfire", "volcano",

    # Mental health / self-harm
    "suicide", "want to die", "ending my life", "self harm", "i want to kill myself",
    "depression", "i can't take it", "i feel hopeless",

    # Panic situations
    "panic", "i'm scared", "they're coming", "i can't move", "they're chasing me",
    "trapped", "locked in", "can't get out", "i'm hiding", "they broke in",

    # Miscellaneous
    "child missing", "lost child", "elderly missing", "abandoned", "suspicious activity",
    "dangerous person", "bomb", "threat", "terrorist", "screaming", "crying for help"
]

UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load voice classifier model
model_path = "assets/models/voice_classifier.pkl"
clf = joblib.load(model_path)

# Helpers
def transcribe_audio(file_path):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(file_path)
    wav_path = file_path.rsplit('.', 1)[0] + '.wav'
    audio.export(wav_path, format='wav')
    with sr.AudioFile(wav_path) as source:
        audio_data = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio_data).lower()
        except:
            return ""

def simulate_phone():
    return "+1" + ''.join(str(random.randint(0, 9)) for _ in range(10))

def extract_embedding(audio_path):
    try:
        y, sr = librosa.load(audio_path, sr=16000)
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        return np.mean(mfcc.T, axis=0)
    except Exception as e:
        print(f"[ERROR] {e}")
        return None

def classify_audio(audio_path):
    emb = extract_embedding(audio_path)
    if emb is not None:
        pred = clf.predict([emb])[0]
        return "REAL (Human)" if pred == 1 else "FAKE (AI-generated)"
    return "Unable to classify"

@app.route('/', methods=['GET', 'POST'])
def index():
    emergency_audios = []
    keyword_map = {}
    caller_locations = []
    phone_number_map = {}
    classifier_map = {}
    trace_requested = request.form.get('trace') == 'true'

    if request.method == 'POST':
        if trace_requested:
            emergency_audios = json.loads(request.form.get('emergency_audios', '[]'))
            keyword_map = json.loads(request.form.get('keyword_map', '{}'))
            phone_number_map = json.loads(request.form.get('phone_number_map', '{}'))
            caller_locations = json.loads(request.form.get('caller_locations', '[]'))
            classifier_map = json.loads(request.form.get('classifier_map', '{}'))
        else:
            files = request.files.getlist('audio_files')
            for file in files:
                if file and file.filename:
                    ext = file.filename.rsplit('.', 1)[-1].lower()
                    if ext in ['mp3', 'wav', 'm4a', 'mp4']:
                        filename = f"{uuid.uuid4().hex}.{ext}"
                        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                        file.save(save_path)

                        transcript = transcribe_audio(save_path)
                        found_keywords = [kw for kw in EMERGENCY_KEYWORDS if kw in transcript]
                        
                        if found_keywords:
                            emergency_audios.append(filename)
                            keyword_map[filename] = found_keywords
                            phone_number = ''.join(c for c in file.filename if c.isdigit() or c == '+') or simulate_phone()
                            phone_number_map[filename] = phone_number
                            caller_locations.append(spoof_caller_location(get_device_location()))
                            classifier_map[filename] = classify_audio(save_path)

    callie = get_device_location()

    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HarkVeil | Emergency Voice Classifier</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: #2E2E2E;
            color: #ffffff;
            margin: 0;
            padding: 0;
        }

        header {
            background-color: #E6E6FA;
            padding: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
        }

        header img {
            height: 100px;
            margin-right: 15px;
        }

        header h1 {
            font-size: 50px;
            color: #00CED1;
            margin: 0;
        }

        main {
            padding: 30px;
            max-width: 900px;
            margin: 0 auto;
        }

        h2 {
            color: #E63946;
            margin-bottom: 10px;
        }

        form.upload-form {
            background-color: #9CAF88;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 6px 6px 12px #1c1c1c, -6px -6px 12px #4a4a4a;
            margin-bottom: 30px;
        }

        input[type="file"] {
            background: #fff;
            padding: 10px;
            border-radius: 10px;
            border: none;
            width: 100%;
            margin-bottom: 15px;
        }

        button {
            background: linear-gradient(to right, #E63946, #ff6b6b);
            border: none;
            padding: 12px 25px;
            border-radius: 12px;
            color: white;
            font-size: 16px;
            cursor: pointer;
            box-shadow: 3px 3px 8px #1c1c1c;
            transition: transform 0.2s ease;
        }

        button:hover {
            transform: translateY(-2px);
            box-shadow: 5px 5px 12px #1c1c1c;
        }

        .audio-card {
            background: #1F1F1F;
            margin: 20px 0;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 8px 8px 15px #1c1c1c, -4px -4px 10px #3a3a3a;
        }

        .audio-card strong {
            color: #00CED1;
        }

        .keywords {
            color: #E63946;
        }

        .classifier {
            color: #00CED1;
            font-weight: bold;
        }

        audio {
            width: 100%;
            margin-top: 10px;
            border-radius: 10px;
            background-color: #014D4E;
        }

        #map {
            height: 500px;
            border-radius: 15px;
            margin-top: 40px;
            box-shadow: 8px 8px 15px #1c1c1c, -4px -4px 10px #3a3a3a;
        }

        .trace-form {
            margin-top: 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <header>
        <img src="{{ url_for('static', filename='logo.png') }}" alt="HarkVeil Logo">
        <h1>HarkVeil</h1>
    </header>

    <main>
        <h2>📞 Emergency Call Simulation</h2>
        <form method="POST" enctype="multipart/form-data" class="upload-form">
            <input type="file" name="audio_files" multiple accept="audio/*" required>
            <button type="submit">Simulate Call</button>
        </form>

        {% if emergency_audios %}
            <h2>🚨 Emergency Calls Detected</h2>
            {% for file in emergency_audios %}
                <div class="audio-card">
                    <strong>Phone:</strong> {{ phone_number_map[file] }}<br>
                    <strong>Keywords:</strong> <span class="keywords">{{ keyword_map[file] | join(', ') }}</span><br>
                    <strong>Voice Type:</strong> <span class="classifier">{{ classifier_map[file] }}</span><br>
                    <audio controls>
                        <source src="{{ url_for('static', filename='uploads/' + file) }}">
                        Your browser does not support audio.
                    </audio>
                </div>
            {% endfor %}

            <form method="POST" class="trace-form">
                <input type="hidden" name="trace" value="true">
                <input type="hidden" name="emergency_audios" value='{{ emergency_audios | tojson }}'>
                <input type="hidden" name="caller_locations" value='{{ caller_locations | tojson }}'>
                <input type="hidden" name="phone_number_map" value='{{ phone_number_map | tojson }}'>
                <input type="hidden" name="keyword_map" value='{{ keyword_map | tojson }}'>
                <input type="hidden" name="classifier_map" value='{{ classifier_map | tojson }}'>
                <button type="submit">Trace The Calls</button>
            </form>
        {% endif %}

        {% if trace_requested and emergency_audios and caller_locations %}
            <div id="map"></div>
            <script>
                var map = L.map('map').setView([{{ callie.latitude }}, {{ callie.longitude }}], 13);
                L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
                    maxZoom: 19,
                    attribution: '© OpenStreetMap contributors'
                }).addTo(map);

                L.marker([{{ callie.latitude }}, {{ callie.longitude }}], {
                    icon: L.icon({ iconUrl: 'https://maps.gstatic.com/mapfiles/ms2/micons/blue-dot.png' })
                }).addTo(map).bindPopup("📍 Callie (Your Location)");

                const colors = ['red', 'green', 'orange', 'purple'];
                const callers = {{ caller_locations|tojson }};
                const phoneNumbers = {{ phone_number_map|tojson }};
                const filenames = {{ emergency_audios|tojson }};

                callers.forEach((caller, i) => {
                    const filename = filenames[i];
                    const phone = phoneNumbers[filename] || "Unknown";

                    L.marker([caller.latitude, caller.longitude], {
                        icon: L.icon({
                            iconUrl: `https://maps.gstatic.com/mapfiles/ms2/micons/${colors[i % colors.length]}-dot.png`,
                            iconSize: [32, 32]
                        })
                    }).addTo(map).bindPopup("📞 " + phone);
                });
            </script>
        {% endif %}
    </main>
</body>
</html>

    ''',
    emergency_audios=emergency_audios,
    keyword_map=keyword_map,
    callie=callie,
    caller_locations=caller_locations,
    phone_number_map=phone_number_map,
    classifier_map=classifier_map,
    trace_requested=trace_requested)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
