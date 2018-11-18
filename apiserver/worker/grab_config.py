"""
Grab worker configuration from GCloud instance attributes.
"""
import json
import requests

with open("config.json", "w") as configfile:
    json.dump({
        "MANAGER_URL": "http://localhost:5001/v1/coordinator/",
        "SECRET_FOLDER": "",
        "CAPABILITIES": [],
        "MAX_BOT_UPLOAD_SIZE": 104857600,
    }, configfile)
