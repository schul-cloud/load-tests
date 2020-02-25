# Schul-Cloud load tests

Load tests for Schul-Cloud application.

## Python

```
pip install -r requirements.txt
locust -f ./locustfile.py --no-web -c 20 --run-time 30s --host https://hackathon.schul-cloud.org
```

## Docker

```
pip install -r requirements.txt
docker run -it --rm -v "$(pwd)":/app -e "LOCUSTFILE_PATH=/app/locustfile.py" -e "LOCUST_OPTS=--no-web -c 20 --run-time 30s" -e "TARGET_URL=https://hackathon.schul-cloud.org" locustio/locust:0.14.4
```
