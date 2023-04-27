import json
import os

DATA_DIR = os.path.dirname(os.path.realpath(__file__)) + "/data"

def load_json_data(file_path: str):
    with open(f"{DATA_DIR}/{file_path}", encoding="utf8") as fp:
        json.load(fp)

def load_data(file_path: str):
    with open(f"{DATA_DIR}/{file_path}", encoding="utf8") as fp:
        return fp.read()
