### What is coded?
1. Consumer group reading messages from kafka 1
2. Consumer group reading messages from kafka 2

Things like config store, external CRM calls, translator, etc. are stubbed.

I have implemented a basic token bucket rate limiter in python for this assignment.


### How to run

### Option 1 : With docker

``` commandline
docker build -t sync-pipeline:latest .
docker run --rm sync-pipeline:latest
```


or with docker compose
```commandline
docker compose up --build
```

### Option 2 : with python
python version should be 3.11 or above

```commandline
cd sync_pipeline // or your dir name

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python3 -m src.main
```

### How to run tests?
```commandline
cd sync_pipeline // or your dir name
python -m pytest tests/ -v
```


