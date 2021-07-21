import sys
import logging
import random
import yaml
import os

from locust import HttpUser, TaskSet, between, task
from locustfile import WebsiteTasks
from urllib.parse import urlparse

class AdminUser(HttpUser):
    weight = 1
    tasks = None
    wait_time = between(5, 15)

    txn_id = ""
    user_type = "admin"
    next_batch = ""
    filter_id = None
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