import json
import os
import time
from datetime import datetime

import httpx
import pandas as pd

BASE_URL = "https://dev-task.elancoapps.com/data"
SIGHTINGS_FILE = "data/sightings.csv"
SUMMARY_FILE = "data/summary.json"


class SourceError(Exception):
    pass


# call the api, retrying if it fails
def fetch_json(client, path):
    for attempt in range(1, 5):
        try:
            response = client.get(BASE_URL + path)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as error:
            print(f"Attempt {attempt} failed: {error}")
            if attempt < 4:
                time.sleep(2 ** attempt)
    raise SourceError(f"Could not get {path} after 4 attempts")


