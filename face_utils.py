# face_utils.py
import face_recognition
import numpy as np
import pickle
from pathlib import Path
from PIL import Image
import io

ENCODINGS_PATH = Path("encodings.pkl")

def load_encodings():
    if ENCODINGS_PATH.exists():
        with open(ENCODINGS_PATH, "rb") as f:
            return pickle.load(f)
    return {}  # {student_id: {"name": name, "encoding": np.array([...])}}

def save_encodings(encodings_dict):
    with open(ENCODINGS_PATH, "wb") as f:
        pickle.dump(encodings_dict, f)

def image_bytes_to_array(image_bytes: bytes):
    # returns RGB numpy array usable by face_recognition
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    return np.array(img)

def register_face(student_id: str, name: str, image_bytes: bytes):
    img_arr = image_bytes_to_array(image_bytes)
    locs = face_recognition.face_locations(img_arr)
    if len(locs) == 0:
        raise ValueError("No face detected in the registration image.")
    # take the first face
    enc = face_recognition.face_encodings(img_arr, known_face_locations=locs)[0]
    encodings = load_encodings()
    encodings[student_id] = {"name": name, "encoding": enc}
    save_encodings(encodings)

def match_face(image_bytes: bytes, tolerance=0.5):
    img_arr = image_bytes_to_array(image_bytes)
    locs = face_recognition.face_locations(img_arr)
    if len(locs) == 0:
        return None  # no face detected
    encs = face_recognition.face_encodings(img_arr, known_face_locations=locs)
    encodings = load_encodings()
    if not encodings:
        return None
    known_ids = list(encodings.keys())
    known_encs = [encodings[sid]["encoding"] for sid in known_ids]
    for face_enc in encs:
        distances = face_recognition.face_distance(known_encs, face_enc)
        best_idx = np.argmin(distances)
        if distances[best_idx] <= tolerance:
            sid = known_ids[best_idx]
            return {"student_id": sid, "name": encodings[sid]["name"], "distance": float(distances[best_idx])}
    return None
