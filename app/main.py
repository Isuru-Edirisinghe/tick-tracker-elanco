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


# search and filter by time range and location
@app.get("/sightings")
def search_sightings(start_date: str = None, end_date: str = None, city: str = None,
                     species: str = None, page: int = 1, page_size: int = 50):
    if page < 1 or page_size < 1 or page_size > 200:
        raise HTTPException(status_code=400, detail="page must be 1+ and page_size 1-200")

    df = get_filtered_data(start_date, end_date, city, species)
    df = df.sort_values("date", ascending=False)

    start = (page - 1) * page_size
    results = df.iloc[start: start + page_size].copy()
    results["date"] = results["date"].dt.strftime("%Y-%m-%dT%H:%M:%S")

    return {"total": len(df), "page": page, "results": results.to_dict(orient="records")}


