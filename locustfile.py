import sys
import logging
import random
from locust.user.users import User
import yaml
import os

from locust import HttpUser, between
from pupil import WebsiteTasks
from urllib.parse import urlparse
from bbbTaskSet import bbbTaskSet
from docTaskSet import docTaskSet

tasksSets = [WebsiteTasks, bbbTaskSet, docTaskSet]
wait_time = between(5, 15)
class PupilUser(HttpUser):
    weight = 5
    wait_time = wait_time
    tasks = tasksSets
    user_type = "pupil"
    login_credentials = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        getUserCredentials(self)

class AdminUser(HttpUser):
    weight = 1
    tasks = tasksSets
    wait_time = wait_time
    user_type = "admin"
    login_credentials = None

    def __init__(self, *args, **kwargs):
        super(AdminUser, self).__init__(*args, **kwargs)

        getUserCredentials(self)

class TeacherUser(HttpUser):
    weight = 3
    tasks = tasksSets
    wait_time = wait_time
    user_type = "teacher"
    login_credentials = None

    def __init__(self, *args, **kwargs):
        super(TeacherUser, self).__init__(*args, **kwargs)
        
        getUserCredentials(self)

        

def getUserCredentials(user):
    logger = logging.getLogger(__name__)

    hostname = urlparse(user.host).hostname
    filename = "./users_" + hostname + ".yaml"
    if not os.path.exists(filename):
        logger.error("File does not exist: " + filename)
        sys.exit(1)

    with open(filename, 'r') as file:
        yaml_loaded = yaml.safe_load(file)
        if (yaml_loaded != None) and (user.user_type in yaml_loaded):
            user.login_credentials = random.choice(yaml_loaded[user.user_type])

    if user.login_credentials == None:
        logger.info("No %s users found in " + filename, user.user_type)
