import json
import logging
import os
import random
import sys
import yaml

from bs4 import BeautifulSoup
from locust import HttpUser, TaskSet, between, task
from locust.exception import LocustError, CatchResponseError, ResponseError
from urllib.parse import urlparse

def is_static_file(f):
    if f.endswith(".css") or f.endswith(".png"):
        return True
    else:
        return False

def fetch_static_assets(session, response):
    resource_urls = set()
    soup = BeautifulSoup(response.text, "html.parser")

    for src in soup.find_all(src=True):
        url = src['src']
        if url.endswith(".js"):
            resource_urls.add(url)
 
    for res in soup.find_all(href=True):
        url = res['href']
        if is_static_file(url):
            resource_urls.add(url)    
    
    for use_url in resource_urls:
        with session.client.get(use_url, catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                    response.failure("Failed! (username: " + session.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")


class WebsiteTasks(TaskSet):
    csrf_token = None

    def on_start(self):
        if self.user.login_credentials == None:
            self.interrupt(reschedule=False)

        with self.client.get("/login/", catch_response=True) as login_get_response:
            soup = BeautifulSoup(login_get_response.text, "html.parser")
            self.csrf_token = soup.select_one('meta[name="csrfToken"]')['content']

            login_data = {
                "challenge": "",
                "username": self.user.login_credentials["email"],
                "password": self.user.login_credentials["password"],
                "_csrf": self.csrf_token
            }
            with self.client.request("POST", "/login/", data=login_data, catch_response=True, allow_redirects=False)  as login_post_response:
                if (login_post_response.status_code != 302) or not login_post_response.headers.get('location').startswith("/login/success"):
                    login_post_response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(login_post_response.status_code)+", header: "+str(login_post_response.headers)+")")
    def on_stop(self):
        self.client.get("/logout/", allow_redirects=True)
        self.csrf_token = None

    @task
    def index(self):
        self.client.get("/")

    @task
    def calendar(self):
        with self.client.get("/calendar/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def account(self):
        with self.client.get("/account/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def dashboard(self):
        with self.client.get("/dashboard/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+")")
            else:
                fetch_static_assets(self, response)

    @task
    def courses(self):
        with self.client.get("/courses/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)
                                


    @task
    def courses_add(self):
        with self.client.get("/courses/add/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                soup = BeautifulSoup(response.text, "html.parser")
                #print(soup)
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                #print(response)
                fetch_static_assets(self, response)
    @task
    def courses_add_course(self):
        #print(self.user)
        #print(self.user_type)
        if self.user != "pupil" :
            course_data = {
                "stage":"on",
                "_method":"post",
                "schoolId":"5f2987e020834114b8efd6f8",
                "name":"Loadtest",
                "color":"#ACACAC",
                "teacherIds":"0000d231816abba584714c9e",
                "startDate":"01.08.2020",
                "untilDate":"31.07.2021",
                "_csrf": self.csrf_token
            }
            with self.client.request("POST", "/courses/", data=course_data, catch_response=True, allow_redirects=True) as response:
                soup = BeautifulSoup(response.text, "html.parser")
                #print(soup)
                if response.status_code != 200:
                    response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
                else:
                    json_object = json.loads(soup.string)
                    #print(json_object["createdCourse"]["id"])
                    with self.client.request("DELETE", 
                        "/courses/" + json_object["createdCourse"]["id"] + "/" , 
                        catch_response=True, 
                        allow_redirects=True, 
                        headers = {
                            "accept": "*/*",
                            "accept-language": "en-US,en;q=0.9",
                            "csrf-token": self.csrf_token,
                            "sec-fetch-dest": "empty",
                            "sec-fetch-mode": "cors",
                            "sec-fetch-site": "same-origin",
                            "x-requested-with": "XMLHttpRequest",
                            "referrer" : ("https://staging.niedersachsen.hpi-schul-cloud.org/courses/"+ json_object["createdCourse"]["id"] +"/edit"),
                            "Origin" : "https://staging.niedersachsen.hpi-schul-cloud.org"
                        }
                    ) as response:

                        if response.status_code != 200:
                            response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
        else:
            response.status_code = 200

    @task
    def homework(self):
        with self.client.get("/homework/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")                
            else:
                fetch_static_assets(self, response)

    @task
    def homework_new(self):
        with self.client.get("/homework/new/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def homework_asked(self):
        with self.client.get("/homework/asked/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def homework_private(self):
        with self.client.get("/homework/private/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def homework_archive(self):
        with self.client.get("/homework/archive/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def files(self):
        with self.client.get("/files/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def files_my(self):
        with self.client.get("/files/my/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def files_courses(self):
        with self.client.get("/files/courses/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def files_shared(self):
        with self.client.get("/files/shared/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def files_shared(self):
        with self.client.get("/files/shared/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def news(self):
        with self.client.get("/news/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def newsnew(self):
        with self.client.get("/news/new", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def addons(self):
        with self.client.get("/addons/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

    @task
    def content(self):
        with self.client.get("/content/", catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(self, response)

class AdminUser(HttpUser):
    weight = 1
    tasks = [WebsiteTasks]
    wait_time = between(5, 15)

    user_type = "admin"
    login_credentials = None

    def __init__(self, *args, **kwargs):
        super(AdminUser, self).__init__(*args, **kwargs)

        logger = logging.getLogger(__name__)

        hostname = urlparse(self.host).hostname
        filename = "./users_" + hostname + ".yaml"
        if not os.path.exists(filename):
            logger.error("File does not exist: " + filename)
            sys.exit(1)

        with open(filename, 'r') as file:
            yaml_loaded = yaml.safe_load(file)
            if (yaml_loaded != None) and (self.user_type in yaml_loaded):
                self.login_credentials = random.choice(yaml_loaded[self.user_type])

        if self.login_credentials == None:
            logger.info("No %s users found in " + filename, self.user_type)

class TeacherUser(HttpUser):
    weight = 3
    tasks = [WebsiteTasks]
    wait_time = between(5, 15)

    user_type = "teacher"
    login_credentials = None

    def __init__(self, *args, **kwargs):
        super(TeacherUser, self).__init__(*args, **kwargs)

        logger = logging.getLogger(__name__)

        hostname = urlparse(self.host).hostname
        filename = "./users_" + hostname + ".yaml"
        if not os.path.exists(filename):
            logger.error("File does not exist: " + filename)
            sys.exit(1)

        with open(filename, 'r') as file:
            yaml_loaded = yaml.safe_load(file)
            if (yaml_loaded != None) and (self.user_type in yaml_loaded):
                self.login_credentials = random.choice(yaml_loaded[self.user_type])

        if self.login_credentials == None:
            logger.info("No %s users found in " + filename, self.user_type)

class PupilUser(HttpUser):
    weight = 5
    tasks = [WebsiteTasks]
    wait_time = between(5, 15)

    user_type = "pupil"
    login_credentials = None

    def __init__(self, *args, **kwargs):
        super(PupilUser, self).__init__(*args, **kwargs)

        logger = logging.getLogger(__name__)

        hostname = urlparse(self.host).hostname
        filename = "./users_" + hostname + ".yaml"
        if not os.path.exists(filename):
            logger.error("File does not exist: " + filename)
            sys.exit(1)

        with open(filename, 'r') as file:
            yaml_loaded = yaml.safe_load(file)
            if (yaml_loaded != None) and (self.user_type in yaml_loaded):
                self.login_credentials = random.choice(yaml_loaded[self.user_type])

        if self.login_credentials == None:
            logger.info("No %s users found in " + filename, self.user_type)
