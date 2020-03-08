# Schul-Cloud load tests

Load tests for Schul-Cloud application.

## Requirements

- Python (>= 3.6.10)
- Docker (>= 19.03.5, optional)

Create a YAML file with user credentials (email, password). Filename should be `users_${HOSTNAME}.yaml`.

Example for `HOSTNAME=hackathon.schul-cloud.org`:
```
# file: users_hackathon.schul-cloud.org.yaml
---
admin:
  - email: admin@schul-cloud.org
    password: foo
teacher:
  - email: lehrer@schul-cloud.org
    password: bar
pupil:
  - email: schueler@schul-cloud.org
    password: baz
```

## Run the load tests

### Python

```
pip install -r requirements.txt
locust -f ./locustfile.py --no-web --clients 20 --run-time 30s --host https://hackathon.schul-cloud.org
```

### Docker

```
docker run -it --rm --entrypoint /bin/sh -v "$(pwd)":/app -w /app locustio/locust:0.14.4
pip install -r requirements.txt
locust -f ./locustfile.py --no-web --clients 20 --run-time 30s --host https://hackathon.schul-cloud.org --logfile $(date '+%Y-%m-%d-%H:%M:%S')-hackathon.log --csv=$(date '+%Y-%m-%d-%H:%M:%S')-hackathon
```
