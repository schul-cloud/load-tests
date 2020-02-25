import json
import logging
import os
import random
import sys
import yaml

from bs4 import BeautifulSoup
from locust import HttpLocust, TaskSet, between, task
from locust.exception import LocustError
from urllib.parse import urlparse

class WebsiteTasks(TaskSet):
    csrf_token = None
    user = None

    def on_start(self):
        if len(self.locust.users) > 0:
            self.user = random.choice(self.locust.users)

            with self.client.get("/login/", catch_response=True) as response:
                soup = BeautifulSoup(response.text, "html.parser")
                self.csrf_token = soup.select_one('meta[name="csrfToken"]')['content']

                login_data = {
                    "challenge": "",
                    "username": self.user["email"],
                    "password": self.user["password"],
                    "_csrf": self.csrf_token
                }
                self.client.post("/login/", login_data, allow_redirects=False)

    def on_stop(self):
        self.client.get("/logout/", allow_redirects=False)
        self.csrf_token = None
        self.user = None

    @task
    def index(self):
        self.client.get("/")

    @task
    def account(self):
        with self.client.get("/account/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")

    @task
    def dashboard(self):
        with self.client.get("/dashboard/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")

    @task
    def courses(self):
        with self.client.get("/courses/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")
    def courses_add(self):
        with self.client.get("/courses/add/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")

    @task
    def homework(self):
        with self.client.get("/homework/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")
    def homework_new(self):
        with self.client.get("/homework/new/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")
    @task
    def homework_asked(self):
        with self.client.get("/homework/asked/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")
    @task
    def homework_private(self):
        with self.client.get("/homework/private/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")
    @task
    def homework_archive(self):
        with self.client.get("/homework/archive/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")

    @task
    def files(self):
        with self.client.get("/files/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")
    @task
    def files_my(self):
        with self.client.get("/files/my/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")
    @task
    def files_courses(self):
        with self.client.get("/files/courses/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")
    @task
    def files_shared(self):
        with self.client.get("/files/shared/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")

    @task
    def news(self):
        with self.client.get("/news/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")

    @task
    def calendar(self):
        with self.client.get("/calendar/", catch_response=True, allow_redirects=False) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user["email"] + ")")

class AdminUser(HttpLocust):
    weight = 1
    task_set = WebsiteTasks
    wait_time = between(5, 15)

    users = []

    def __init__(self):
        super(AdminUser, self).__init__()

        logger = logging.getLogger(__name__)

        hostname = urlparse(self.host).netloc
        filename = "./users_" + hostname + ".yaml"
        if not os.path.exists(filename):
            logger.error("File does not exist: " + filename)
            sys.exit(1)

        with open(filename, 'r') as file:
            yaml_loaded = yaml.safe_load(file)
            if "admin" in yaml_loaded:
                self.users = yaml_loaded["admin"]

        if len(self.users) == 0:
            logger.error("No admin users found in " + filename)
            sys.exit(1)

class TeacherUser(HttpLocust):
    weight = 3
    task_set = WebsiteTasks
    wait_time = between(5, 15)

    users = []

    def __init__(self):
        super(TeacherUser, self).__init__()

        logger = logging.getLogger(__name__)

        hostname = urlparse(self.host).netloc
        filename = "./users_" + hostname + ".yaml"
        if not os.path.exists(filename):
            logger.error("File does not exist: " + filename)
            sys.exit(1)

        with open(filename, 'r') as file:
            yaml_loaded = yaml.safe_load(file)
            if "teacher" in yaml_loaded:
                self.users = yaml_loaded["teacher"]

        if len(self.users) == 0:
            logger.error("No teacher users found in " + filename)
            sys.exit(1)

class PupilUser(HttpLocust):
    weight = 5
    task_set = WebsiteTasks
    wait_time = between(5, 15)

    users = []

    def __init__(self):
        super(PupilUser, self).__init__()

        logger = logging.getLogger(__name__)

        hostname = urlparse(self.host).netloc
        filename = "./users_" + hostname + ".yaml"
        if not os.path.exists(filename):
            logger.error("File does not exist: " + filename)
            sys.exit(1)

        with open(filename, 'r') as file:
            yaml_loaded = yaml.safe_load(file)
            if "pupil" in yaml_loaded:
                self.users = yaml_loaded["pupil"]

        if len(self.users) == 0:
            logger.error("No pupil users found in " + filename)
            sys.exit(1)
