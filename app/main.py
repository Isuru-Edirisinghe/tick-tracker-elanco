import pandas as pd
from fastapi import FastAPI, HTTPException

from . import ingestion

app = FastAPI(title="UK Tick Tracker API")

sightings = pd.DataFrame()
summary = {}


# load saved data if we have it, otherwise download it
def load_data():
    global sightings, summary

    saved = ingestion.load_from_disk()
    if saved is not None:
        sightings, summary = saved
        return

    try:
        sightings, summary = ingestion.run_sync()
    except ingestion.SourceError as error:
        print("Could not download data:", error)


load_data()


# apply the filters and return the matching rows
def get_filtered_data(start_date, end_date, city, species):
    if sightings.empty:
        raise HTTPException(status_code=503, detail="No data loaded. Try POST /sync later.")

    df = sightings

    if start_date:
        try:
            df = df[df["date"] >= pd.to_datetime(start_date)]
        except ValueError:
            raise HTTPException(status_code=400, detail="start_date must look like 2022-01-31")

    if end_date:
        try:
            df = df[df["date"] < pd.to_datetime(end_date) + pd.Timedelta(days=1)]
        except ValueError:
            raise HTTPException(status_code=400, detail="end_date must look like 2022-01-31")

    if city:
        df = df[df["location"].str.lower() == city.lower()]
    if species:
        df = df[df["species"].str.lower() == species.lower()]

    return df


@app.get("/health")
def health():
    return {"sightings_loaded": len(sightings), "last_synced": summary.get("synced_at")}


@app.post("/sync")
def sync():
    global sightings, summary
    try:
        sightings, summary = ingestion.run_sync()
    except ingestion.SourceError as error:
        raise HTTPException(status_code=503, detail=f"Sync failed: {error}. Old data is still being served.")
    return {"message": "Sync complete", "summary": summary}


@app.get("/data-quality")
def data_quality():
    return summary


