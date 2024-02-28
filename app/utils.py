import base64
import os
import pickle
import json
import shutil
from uuid import uuid4

TMP_DIR = "/tmp"
os.makedirs(TMP_DIR, exist_ok=True)


def open_object(object_path):
    with open(object_path, mode='rb') as f:
        obj = pickle.load(f)

    return obj


def save_object(object_path, obj):
    with open(object_path, mode='wb') as f:
        pickle.dump(obj, f)


def save_json(object, file_path):
    with open(file_path, mode='w') as f:
        json.dump(object, f, indent=4)


def open_json(file_path):
    with open(file_path, mode='r') as f:
        json_object = json.load(f)
        return json_object


def encode_secret_dict(secret_dict):
    return base64.b64encode(json.dumps(secret_dict).encode('utf-8')).decode('utf-8')


def decode_secret_dict(secret_dict_encoded):
    return json.loads(base64.b64decode(secret_dict_encoded.encode('utf-8')).decode('utf-8'))


def save_file(file):
    tmp_dir = str(uuid4())
    file_path = f"{TMP_DIR}/{tmp_dir}/{file.filename}"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return file_path
