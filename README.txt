UK Tick Tracker - Backend
Isuru Edirisinghe

What this is
------------
This is my submission for the Elanco placement technical task. It's a
backend API for a UK tick sighting tracker, similar to Elanco's
Parvovirus Tracker in the US. It pulls the sighting data from the
Elanco API, cleans it up, and lets you search it and see some basic
reports (sightings per city and trends over time).

The demo video is in this repo: demo_video.mp4


How to run it
-------------
You need Python 3.

    git clone https://github.com/Isuru-Edirisinghe/tick-tracker-elanco.git
    cd tick-tracker-elanco
    python -m venv .venv

Activate the virtual environment:
    Mac/Linux:   source .venv/bin/activate
    Git Bash:    source .venv/Scripts/activate
    PowerShell:  .venv\Scripts\Activate.ps1

Then:

    pip install -r requirements.txt
    uvicorn app.main:app --reload

Go to http://127.0.0.1:8000/docs and you can try every endpoint from
the browser. The first time it starts it downloads the data
automatically. You can also run "python -m app.ingestion" on its own
to just download and clean the data.


What's in the project
---------------------
app/ingestion.py   gets the data from the Elanco API, cleans it and
                   removes duplicates
app/main.py        the API endpoints and the filtering
requirements.txt   the libraries I used (fastapi, uvicorn, httpx, pandas)


How it works
------------
The Elanco API can only filter by city or species. It can't filter by
date, count per city or show trends. So instead of calling it for
every request, I download everything once, clean it, and save it to
data/sightings.csv. My API then answers requests from that data using
pandas. A nice side effect is that my API still works if theirs goes
down.

The data only gives a city for each sighting, so I used city as the
location unit for filtering and for the reports. The brief also
mentions "region", so with more time I'd group the cities into proper
UK regions.


Cleaning the data
-----------------
Each record gets checked. If a field is missing or blank, the date
can't be read, or the date is in the future, the record is skipped.
If an id has already been seen, it's skipped as a duplicate. City
names are trimmed and capitalised so they match.

Skipped records are counted, not just dropped, and you can see the
numbers at GET /data-quality. For the dataset I was given: 1000
received, 1000 accepted, 0 duplicates, 0 skipped. That matches the
1000 total the Elanco API says it has. So this data was already clean
and the duplicate and bad record checks didn't actually have anything
to catch this time.


Error handling
--------------
- If a call to the Elanco API fails, it retries up to 4 times, waiting
  2, 4 and then 8 seconds. There's also a 15 second timeout.
- It checks /health first and stops if the Elanco API says it's not
  healthy.
- If POST /sync fails, the old data stays loaded and I return a 503
  with a message.
- If the Elanco API is down when my app starts, the app still starts
  and the endpoints return a 503 saying there's no data yet.
- A bad date, bad granularity or bad page number gives a 400 error
  with a message.


Endpoints
---------
GET  /health            how many sightings are loaded, last sync time
POST /sync              download fresh data from the Elanco API
GET  /data-quality      received / accepted / duplicates / skipped
GET  /sightings         search and filter sightings (paged)
GET  /reports/by-city   number of sightings per city
GET  /reports/trends    sightings per week or per month

/sightings can be filtered by start_date, end_date (like 2022-01-31),
city and species. You can combine any of them, and they're not case
sensitive.
    e.g. /sightings?city=Manchester&start_date=2022-01-01&end_date=2022-12-31

/reports/by-city can be narrowed by start_date, end_date and species.

/reports/trends takes granularity=weekly or monthly (monthly is the
default) and the same filters as /sightings.
    e.g. /reports/trends?granularity=weekly&city=Glasgow


Why I made these choices
------------------------
I used pandas instead of a database because there are only about 1000
records and it keeps the code short and easy to follow. I kept the
data download and the API in separate files so each is easier to
understand. And I skip bad records instead of crashing so one bad row
can't stop the whole download.


Use of AI
---------
I used an AI assistant (Claude) to help plan the project, work out the
structure, and write and debug the code. I went through the code
afterwards so I could understand and explain it. I also asked it what
I could do better with more time. It suggested:

- Using a real database instead of pandas and a CSV file, so data
  could be updated gradually instead of downloaded again each time
- Adding automated tests with pytest
- Saving the reason each record was rejected, not just a count
- Grouping cities into UK regions, ideally with a geocoding or
  postcode service instead of a hand-made list
- Showing empty weeks as 0 in the trends report
- Syncing on a schedule instead of calling POST /sync by hand
- Adding authentication on /sync, plus caching and rate limiting
- Doing the AI/ML extension, like finding hotspot regions
- Building a front end (map and charts) on top of the API

If I had more time I'd start with tests and the database, then try the
extension task. Since the real tracker is crowdsourced, I'd also add a
way for people to report their own sightings.
