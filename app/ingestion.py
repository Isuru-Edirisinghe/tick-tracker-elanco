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


# return a clean record, or None if the record is bad
def clean_record(raw):
    if not isinstance(raw, dict):
        return None

    for field in ["id", "date", "latinName", "species", "location"]:
        if raw.get(field) is None or str(raw[field]).strip() == "":
            return None

    try:
        date = datetime.fromisoformat(str(raw["date"]).strip()).replace(tzinfo=None)
    except ValueError:
        return None

    if date > datetime.now():
        return None

    return {
        "id": str(raw["id"]).strip(),
        "date": date,
        "latin_name": str(raw["latinName"]).strip(),
        "species": str(raw["species"]).strip(),
        "location": str(raw["location"]).strip().title(),
    }


# clean every record and remove duplicates
def process_records(raw_records):
    good = []
    seen_ids = set()
    duplicates = 0
    bad = 0

    for raw in raw_records:
        record = clean_record(raw)
        if record is None:
            bad += 1
            continue
        if record["id"] in seen_ids:
            duplicates += 1
            continue
        seen_ids.add(record["id"])
        good.append(record)

    summary = {
        "received": len(raw_records),
        "accepted": len(good),
        "duplicates_skipped": duplicates,
        "bad_records_skipped": bad,
    }
    return pd.DataFrame(good), summary


