import json
import logging
import os
import random
from re import M
import re
import sys
import jwt
import secrets
import datetime
import calendar
import uuid
from datetime import timezone
from unicodedata import name
from locust.user.task import tag
from requests.sessions import session
import yaml
import time
import webbrowser
import hashlib
import requests

from selenium import webdriver
from selenium.common.exceptions import (ElementClickInterceptedException, NoSuchWindowException)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.by import By
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

def normalGET(session, url):
    with session.client.get(url, catch_response=True, allow_redirects=True) as response:
            if response.status_code != 200:
                response.failure("Failed! (username: " + session.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            else:
                fetch_static_assets(session, response)

def createDoc(session, docdata):
    with session.client.request(   
        "POST",
        "/files/newFile",
        headers = { 
            "Connection"        : "keep-alive",
            "x-requested-with"  : "XMLHttpRequest",
            "csrf-token"        : session.csrf_token,
            "Content-Type"      : "application/x-www-form-urlencoded",
            "Origin"            : session.user.host,
            "Sec-Fetch-Site"    : "same-origin",
            "Sec-Fetch-Mode"    : "cors",
            "Sec-Fetch-Dest"    : "empty",
            "Referer"           : session.user.host + "/files/my/"
        },
        data = docdata,
        catch_response = True, 
        allow_redirects = True
    ) as response:
        if response.status_code != 200:
            response.failure("Failed! (username: " + session.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
        else:
            return response.text
            

def deleteDoc(session, docId):
    data = {
        "id" : docId
    }
    with session.client.request(
        "DELETE",
        "/files/file/",
        headers = {
            "Connection"        : "keep-alive",
            "x-requested-with"  : "XMLHttpRequest",
            "csrf-token"        : session.csrf_token,
            "Origin"            : session.user.host,
            "Sec-Fetch-Site"    : "same-origin",
            "Sec-Fetch-Mode"    : "cors",
            "Sec-Fetch-Dest"    : "empty",
            "Referer"           : session.user.host + "/files/my/"
        },
        data = data,
        catch_response = True, 
        allow_redirects = True,
        name="/files/file/delete"
    ) as response:
        if response.status_code != 200:
            response.failure("Failed! (username: " + session.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")


def createCourse(session, data):
    with session.client.request("POST", "/courses/", data=data, catch_response=True, allow_redirects=True) as response:        
        soup = BeautifulSoup(response.text, "html.parser")
        if response.status_code != 200:
            response.failure("Failed! (username: " + session.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
        else:
            json_object = json.loads(soup.string)
            courseId = str(json_object["createdCourse"]["id"])
            return (courseId)

def deleteCourse(session, courseId):
    with session.client.request("DELETE", 
        "/courses/" + courseId + "/" , 
        catch_response=True, 
        allow_redirects=True,
        name="/courses/delete",
        headers = {
            "accept"            : "*/*",
            "accept-language"   : "en-US,en;q=0.9",
            "csrf-token"        : session.csrf_token,
            "sec-fetch-dest"    : "empty",
            "sec-fetch-mode"    : "cors",
            "sec-fetch-site"    : "same-origin",
            "x-requested-with"  : "XMLHttpRequest",
            "referrer"          : (session.user.host + "/courses/"+ courseId +"/edit"),
            "Origin"            : session.user.host
        }
    ) as response:
        if response.status_code != 200:
            response.failure("Failed! (username: " + session.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")

# Abruf der API, Domain und nuxtversion der SchulCloud über get-request
# [MN, OPS-2471]
def requestWithoutUser(api_domain, domain, nuxt_domain):
    api_req = requests.get(api_domain)
    req = requests.get(domain)
    nuxt_req = requests.get(nuxt_domain)

    if api_req.status_code != 200:
        print("api_req failed")
    else:
        print("api_req successful")

    if req.status_code != 200:
        print("req failed")
    else:
        print("req successful")

    if nuxt_req.status_code != 200:
        print("nuxt_req failed")
    else:
        print("nuxt_req successful")

class WebsiteTasks(TaskSet):
    timeToWaitShort = int(os.environ.get("TIMELONG"))
    timeToWaitLong = int(os.environ.get("TIMESHORT"))
    next_batch = ""
    filter_id = None
    csrf_token = None
    token = None
    user_id = None
    room_ids = []
    
    def on_start(self):

        if self.user.login_credentials == None:
            self.interrupt(reschedule=False)

        with self.client.get("/login/", catch_response=True) as login_get_response:
            soup = BeautifulSoup(login_get_response.text, "html.parser")
            self.csrf_token = soup.select_one('meta[name="csrfToken"]')['content']

            login_data = {
                "challenge" : "",
                "username"  : self.user.login_credentials["email"],
                "password"  : self.user.login_credentials["password"],
                "_csrf"     : self.csrf_token
            }
            with self.client.request("POST", "/login/", data=login_data, catch_response=True, allow_redirects=False)  as login_post_response:
                if (login_post_response.status_code != 302) or not login_post_response.headers.get('location').startswith("/login/success"):
                    login_post_response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(login_post_response.status_code)+", header: "+str(login_post_response.headers)+")")
                else:
                    with self.client.request("GET", "/messenger/token", catch_response=True, allow_redirects=False) as response:
                        if(response.status_code == 200):
                            i = json.loads(response.text)
                            self.token = i["accessToken"]
                            self.user_id = i["userId"]
                    with self.client.get("/courses/" , catch_response=True, allow_redirects=True) as response:
                        if(response.status_code == 200):
                            soup = BeautifulSoup(response.text, "html.parser")
                            for room_id in soup.find_all('article'):
                                self.room_ids.append(room_id.get('data-loclink').removeprefix("/courses/"))

    def on_stop(self):
        self.client.get("/logout/", allow_redirects=True)
        self.csrf_token = None

    @tag('sc')
    @task
    def index(self):
        self.client.get("/")

    @tag('sc')
    @task
    def calendar(self):
        normalGET(self, "/calendar/")

    @tag('sc')
    @task
    def account(self):
        normalGET(self, "/account/")

    @tag('sc')
    @task
    def dashboard(self):
        normalGET(self, "/dashboard/")

    @tag('sc')
    @task
    def courses(self):
        normalGET(self, "/courses/")

    @tag('sc')
    @task
    def courses_add(self):
        normalGET(self, "/courses/add/")
    
    @tag('sc')
    @task
    def homework(self):
        normalGET(self, "/homework/")

    @tag('sc')
    @task
    def homework_new(self):
        normalGET(self, "/homework/new/")
        
    @tag('sc')
    @task
    def homework_asked(self):
        normalGET(self, "/homework/asked/")

    @tag('sc')
    @task
    def homework_private(self):
        normalGET(self, "/homework/private/")

    @tag('sc')
    @task
    def homework_archive(self):
        normalGET(self, "/homework/archive/")

    @tag('sc')
    @task
    def files(self):
        normalGET(self, "/files/")

    @tag('sc')
    @task
    def files_my(self):
        normalGET(self, "/files/my/")

    @tag('sc')
    @task
    def files_courses(self):
        normalGET(self, "/files/courses/")

    @tag('sc')
    @task
    def files_shared(self):
        normalGET(self, "/files/shared/")

    @tag('sc')
    @task
    def files_shared(self):
        normalGET(self, "/files/shared/")

    @tag('sc')
    @task
    def news(self):
        normalGET(self, "/news/")

    @tag('sc')
    @task
    def newsnew(self):
        normalGET(self, "/news/new")
    
    @tag('sc')
    @task
    def addons(self):
        normalGET(self, "/addons/")

    @tag('sc')
    @task
    def content(self):
        normalGET(self, "/content/")

    @tag('test')
    @tag('sc')
    @tag('course')
    @task
    def courses_add_Lernstore(self):
        with self.client.request(
            "GET",
            "/",
            catch_response=True, 
            allow_redirects=True
        ) as response:
            print(response.text)
        if "schueler" in str(self.user.login_credentials["email"]):
            pass
        else:
            mainHost = self.user.host
            ### Create Course ###
            course_data = {
                "stage"                 :"on",
                "_method"               :"post",
                "schoolId"              :"5f2987e020834114b8efd6f8",
                "name"                  :"Loadtest Lernstore",
                "color"                 :"#ACACAC",
                "teacherIds"            :"0000d231816abba584714c9e",
                "startDate"             :"01.08.2020",
                "untilDate"             :"31.07.2022",
                "times[0][weekday]"     : "0",
                "times[0][startTime]"   : "12:00",
                "times[0][duration]"    : "90",
                "times[0][room]"        : "1",
                "times[1][weekday]"     : "2",
                "times[1][startTime]"   : "12:00",
                "times[1][duration]"    : "90",
                "times[1][room]"        : "2",
                "_csrf"                 : self.csrf_token
            }
            
            courseId = createCourse(self, course_data)

            ### Add Resources ###
            if "lehrer" in str(self.user.login_credentials["email"]):
                
                thema_data = {
                    "authority"                 : mainHost.replace("https://", ""),
                    "origin"                    : mainHost,
                    "referer"                   : mainHost + "/courses/" + courseId + "/tools/add",
                    "_method"                   : "post",
                    "position"                  : "",
                    "courseId"                  : courseId,
                    "name"                      : "Test1",
                    "contents[0][title]"        : "Test2",
                    "contents[0][hidden]"       : "false",
                    "contents[0][component]"    : "resources",
                    "contents[0][user]"         : "",
                    "_csrf"                     : self.csrf_token
                }

                with self.client.request("POST", 
                    "/courses/" + courseId + "/topics",
                    name="/courses/topics",
                    data=thema_data,
                    catch_response=True, 
                    allow_redirects=True
                ) as response:
                    if response.status_code != 200:
                        response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")

                    data = {
                        "client"            : "Schul-Cloud",
                        "merlinReference"   : "BWS-04983086",
                        "title"             : "Geschichte der Mathematik - Die Sprache des Universums",
                        "url"               : "http://merlin.nibis.de/auth.php?identifier=BWS-04983086"
                    }
                    
                    current_datetime = datetime.datetime.utcnow()
                    current_timetuple = current_datetime.utctimetuple()
                    current_timestamp = calendar.timegm(current_timetuple)

                    payload = {
                        "accountId" : "0000d231816abba584714c9f",
                        "userId"    : "0000d231816abba584714c9e",
                        "schoolId"  : "5f2987e020834114b8efd6f8",
                        "roles"     : ["0000d186816abba584714c98"],
                        "iat"       : current_timestamp,
                        "exp"       : current_timestamp + 2592000,
                        "aud"       : "https://hpi-schul-cloud.de",
                        "iss"       : "feathers",
                        "sub"       : "0000d231816abba584714c9f",
                        "jti"       : str(uuid.uuid4())
                    }

                    tokenB = jwt.encode(payload=payload, key=str(os.environ.get("LERNSTOREKEY")), algorithm="HS256", headers={"alg":"HS256","typ":"access"})

                    with self.client.request("POST",
                        "https://api.staging.niedersachsen.hpi-schul-cloud.org/lessons/" + courseId + "/material",
                        data=data,
                        name="/lessons/material",
                        catch_response=True, 
                        allow_redirects=True,
                        headers = {
                            "authority"         : "api.staging.niedersachsen.hpi-schul-cloud.org",
                            "authorization"     : "Bearer " + tokenB,
                            "origin"            : mainHost,
                            "path"  	        : "/lessons/" + courseId + "/material",
                            "sec-fetch-site"    : "same-site",
                            "sec-fetch-mode"    : "cors",
                            "sec-fetch-dest"    : "empty",
                            "sec-ch-ua-moblie"  : "?0",
                            "sec-ch-ua"         : '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"'
                        }
                    ) as response:
                        print(response.text)
                        if response.status_code != 200:
                            response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")
            ### Delete Course ###
            deleteCourse(self, courseId)


    #@tag('test')
    @tag('sc')
    @tag('course')
    @task
    def courses_add_course(self):
        if "schueler" in str(self.user.login_credentials["email"]):
            pass
        else:
            mainHost = self.user.host
            ### Create Course ###
            course_data = {
                "stage"                 :"on",
                "_method"               :"post",
                "schoolId"              :"5f2987e020834114b8efd6f8",
                "name"                  :"Loadtest",
                "color"                 :"#ACACAC",
                "teacherIds"            :"0000d231816abba584714c9e",
                "startDate"             :"01.08.2020",
                "untilDate"             :"31.07.2022",
                "times[0][weekday]"     : "0",
                "times[0][startTime]"   : "12:00",
                "times[0][duration]"    : "90",
                "times[0][room]"        : "1",
                "times[1][weekday]"     : "2",
                "times[1][startTime]"   : "12:00",
                "times[1][duration]"    : "90",
                "times[1][room]"        : "2",
                "_csrf"                 : self.csrf_token
            }
            
            courseId = createCourse(self, course_data)

            ### Add Etherpads ###
            if "lehrer" in str(self.user.login_credentials["email"]):
                thema_data = {
                    "authority"                         : "staging.niedersachsen.hpi-schul-cloud.org",
                    "origin"                            : mainHost,
                    "referer"                           : mainHost + "/courses/" + courseId + "/tools/add",
                    "_method"                           : "post",
                    "position"                          : "",
                    "courseId"                          : courseId,
                    "name"                              : "Test1",
                    "contents[0][title]"                : "Test2",
                    "contents[0][hidden]"               : "false",
                    "contents[0][component]"            : "Etherpad",
                    "contents[0][user]"                 : "",
                    "contents[0][content][title]"       : "",
                    "contents[0][content][description]" : "Test3",
                    "contents[0][content][url]"         : "https://staging.niedersachsen.hpi-schul-cloud.org/etherpad/pi68ca",
                    "_csrf"                             : self.csrf_token
                }

                with self.client.request("POST", 
                    "/courses/" + courseId + "/topics",
                    name="/courses/topics",
                    data=thema_data,
                    catch_response=True, 
                    allow_redirects=True
                ) as response:
                    if response.status_code != 200:
                        response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")

            ### Add Tool ###
            if "lehrer" in str(self.user.login_credentials["email"]):          
                with self.client.request("POST", 
                    "/courses/" + str(courseId) + "/tools/add",
                    name="/courses/tools/add",
                    headers = {
                        "accept"            : "*/*",
                        "accept-language"   : "en-US,en;q=0.9",
                        "content-type"      : "application/x-www-form-urlencoded; charset=UTF-8",
                        "csrf-token"        : self.csrf_token,
                        "sec-ch-ua"         : "\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"90\", \"Google Chrome\";v=\"90\"",
                        "sec-ch-ua-mobile"  : "?0",
                        "sec-fetch-dest"    : "empty",
                        "sec-fetch-mode"    : "cors",
                        "sec-fetch-site"    : "same-origin",
                        "x-requested-with"  : "XMLHttpRequest"
                    },
                    data = "privacy_permission=anonymous&openNewTab=true&name=bettermarks&url=https://acc.bettermarks.com/Fv1.0/schulcloud/de_ni_staging/login&key=&logo_url=https://acc.bettermarks.com/app/assets/bm-logo.png&isLocal=true&resource_link_id=&lti_version=&lti_message_type=&isTemplate=false&skipConsent=false&createdAt=2021-01-14T13:35:44.689Z&updatedAt=2021-01-14T13:35:44.689Z&__v=0&originTool=600048b0755565002840fde4&courseId=" + str(courseId),
                    catch_response=True, 
                    allow_redirects=True
                ) as response:
                    with self.client.request("GET",
                        "https://acc.bettermarks.com/v1.0/schulcloud/de_ni_staging/login",
                        catch_response=True, 
                        allow_redirects=True
                    ) as response:
                        if response.status_code != 200:
                            response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")

            ### Delete Course ###
            deleteCourse(self, courseId)

    @tag('mm')
    @task
    def message(self):
        txn_id = 0

        if "schueler" in str(self.user.login_credentials["email"]):
            pass
        else:
            mainHost = "https://matrix.niedersachsen.messenger.schule/_matrix/client"
            self.client.headers["authorization"] = "Bearer " + str(self.token)
            self.client.headers["accept"] = "application/json"

            payload = {
                "timeout": 30000
            }

            name = mainHost + "/r0/sync"
            response = self.client.get(mainHost + "/r0/sync", params=payload)#, name=name)
            if response.status_code != 200:
                return

            json_response_dict = response.json()
            if 'next_batch' in json_response_dict:
                self.next_batch = json_response_dict['next_batch']


            # extract rooms
            if 'rooms' in json_response_dict and 'join' in json_response_dict['rooms']:
                room_ids = list(json_response_dict['rooms']['join'].keys())
                if len(room_ids) > 0:
                    self.room_ids = room_ids

            for room_id in self.room_ids:
                message = {
                    "msgtype"   : "m.text",
                    "body"      : "Load Test Message",
                }
                        
                self.client.put(
                    mainHost + "/r0/rooms/" + room_id + "/typing/" + self.user_id,
                    json={"typing": True, "timeout":30000},
                )

                self.client.put(
                    mainHost + "/r0/rooms/" + room_id + "/typing/" + self.user_id,
                    json={"typing": False},
                )

                with self.client.post(
                    mainHost + "/r0/rooms/" + room_id + "/send/m.room.message",
                    json=message,
                ) as response:
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, "html.parser")
                        json_object = json.loads(soup.string)
                        
                        data = {
                            "m.new_content" :{
                                "msgtype"   : "m.text",
                                "body"      : "Load Test !"
                            },
                            "m.relates_to"  :{
                                "rel_type"  : "m.replace",
                                "event_id"  : json_object['event_id']
                            },
                            "msgtype"       : "m.text",
                            "body"          : " * Load Test !"
                        }
                        self.client.post(
                            mainHost + "/r0/rooms/" + room_id + "/send/m.room.message",
                            json=data,
                            #name="https://matrix.niedersachsen.messenger.schule/_matrix/client/r0/rooms/" + room_id + "/send/m.room.message"
                        )# as response
                            #soup = BeautifulSoup(response.text, "html.parser")
                            #json_object = json.loads(soup.string)
                            
                            #content = {
                            #    "reason" : "Loadtest"
                            #}
                            #params = None
                            #path = 'https://matrix.niedersachsen.messenger.schule/_matrix/client/r0/rooms/%s/redact/%s/%s.1' % (
                            #    room_id, json_object['event_id'], txn_id
                            #)

                            #txn_id = txn_id + 1

                            #with self.client.put(path, 
                            #    HTTP/1.1,
                            #    headers = {
                            #        "Content-Type" : "application/json"
                            #    },
                            #    content) as response:
                            #    print(response)
                            

            self.client.get(mainHost + "/versions")

            self.client.get(mainHost + "/r0/voip/turnServer")

            self.client.get(mainHost + "/r0/pushrules/")

            self.client.get(mainHost + "/r0/joined_groups")

            self.client.get(mainHost + "/r0/profile/" + self.user_id)
    
    @tag('bbb')
    @task
    def bBBTest(self):
        bBBKey = os.environ.get("BBBKEY")
        numberRooms = 3
        numberUsers = 6
        host = "https://bbb-1.bbb.staging.messenger.schule"

        driverWB = webdriver.Chrome('.\chromedriver.exe')
        driverWB.get(host)

        counterfirst = 0
        counterTab = 1
        while counterfirst < numberRooms:
            
            timestamp = str(time.time())

            v = "create"
            x = "meetingID=loadtest-" + timestamp + str(counterfirst) + "&name=loadtest-" + str(time.time()) + str(counterfirst) + "&moderatorPW=123&attendeePW=456&lockSettingsDisableMic=true"
            y = host + "/bigbluebutton/api/" + v + "?" + x
            z = str(v) + str(x) + str(bBBKey)
            w = str(y) + "&checksum=" + hashlib.sha1(z.encode()).hexdigest()

            driverWB.get(w)

            countersecond = 0

            v = "join"
            x = "meetingID=loadtest-" + timestamp + str(counterfirst) + "&fullName=loadtest-" + str(counterfirst) + "userMLoadtest-" + str(countersecond) + "&userID=loadtest-" + str(counterfirst) + "userMLoadtest-" + str(countersecond) + "&password=123"
            y = host + "/bigbluebutton/api/" + v + "?" + x
            z = str(v) + str(x) + str(bBBKey)
            w = y + "&checksum=" + hashlib.sha1(z.encode()).hexdigest()
                
            windows = driverWB.window_handles
            driverWB.execute_script("window.open('');")
            driverWB.switch_to.window(driverWB.window_handles[counterTab])
            driverWB.get(w)

            ui_element = "button[aria-label='Listen only']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            time.sleep(self.timeToWaitShort)
            
            ui_element = "tippy-21"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.ID, ui_element)))
            element.click()

            ui_element = "li[aria-labelledby='dropdown-item-label-26']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            ui_element = "input[id='video-modal-input']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.send_keys('https://player.vimeo.com/video/418854539')

            time.sleep(self.timeToWaitShort)

            ui_element = "button[aria-label='Share a new video']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            time.sleep(self.timeToWaitLong) 

            counterTab += 1
            countersecond += 1
            
            while countersecond < numberUsers:
                
                v = "join"
                x = "meetingID=loadtest-" + timestamp + str(counterfirst) + "&fullName=loadtest-" + str(counterfirst) + "userLoadtest-" + str(countersecond) + "&userID=loadtest-" + str(counterfirst) + "userLoadtest-" + str(countersecond) + "&password=456"
                y = host + "/bigbluebutton/api/" + v + "?" + x
                z = str(v) + str(x) + str(bBBKey)
                w = y + "&checksum=" + hashlib.sha1(z.encode()).hexdigest()
                
                windows = driverWB.window_handles
                driverWB.execute_script("window.open('');")
                driverWB.switch_to.window(driverWB.window_handles[counterTab])
                driverWB.get(w)
                
                ui_element = "button[aria-label='Play audio']"
                element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
                element.click()

                time.sleep(self.timeToWaitLong)

                countersecond += 1
                counterTab += 1

            counterfirst += 1
    
        counterfirst = 0
        time.sleep(30)
        while counterfirst < numberRooms:
            
            v = "end"
            x = "meetingID=loadtest-" + timestamp + str(counterfirst) + "&password=123"
            y = host + "/bigbluebutton/api/" + v + "?" + x
            z = str(v) + str(x) + str(self.bBBKey)
            w = str(y) + "&checksum=" + hashlib.sha1(z.encode()).hexdigest()
            
            driverWB.get(w)

            driverWB.quit()
            time.sleep(2)
            counterfirst += 1
    
    @tag('sc')
    @task
    def newTeam(self):
        if "schueler" in str(self.user.login_credentials["email"]):
            pass
        else:
            mainHost = self.user.host
            data = {
                "schoolId"      : "5f2987e020834114b8efd6f8",
                "_method"       : "post",
                "name"          : "Loadtest Team",
                "description"   : "Loadtest Team",
                "messenger"     : "true",
                "rocketChat"    : "true",
                "color"         : "#d32f2f",
                "_csrf"         : self.csrf_token
            }

            with self.client.request(
                "POST",
                mainHost + "/teams/",
                headers = {
                    "authority" : mainHost.replace("https://", ""),
                    "path"      : "/teams/",
                    "origin"    : mainHost,
                    "referer"   : mainHost + "/teams/add"
                },
                data = data,
                catch_response=True, 
                allow_redirects=True 
            ) as response:
                soup = BeautifulSoup(response.text, "html.parser")
                teamIdString = soup.find_all("section", {"class": "section-teams"})
                teamId = str(teamIdString).partition('\n')[0][41:65]

                with self.client.request("DELETE", 
                    "/teams/" + teamId + "/" ,
                    name="/teams/delete",
                    catch_response=True,
                    allow_redirects=True, 
                    headers = {
                        "accept"            : "*/*",
                        "accept-language"   : "en-US,en;q=0.9",
                        "csrf-token"        : self.csrf_token,
                        "sec-fetch-dest"    : "empty",
                        "sec-fetch-mode"    : "cors",
                        "sec-fetch-site"    : "same-origin",
                        "x-requested-with"  : "XMLHttpRequest",
                        "referrer"          : (mainHost + "/teams/" + teamId + "/edit"),
                        "Origin"            : mainHost
                    }
                ) as response:
                    if response.status_code != 200:
                        response.failure("Failed! (username: " + self.user.login_credentials["email"] + ", http-code: "+str(response.status_code)+", header: "+str(response.headers)+ ")")

    @tag('doc')
    @tag('sc')
    @task
    def newFilesDocx(self):
        if "schueler" in str(self.user.login_credentials["email"]):
            pass
        else:
            mainHost = self.user.host
            data = {
                "name"          : "Loadtest docx",
                "type"          : "docx",
                "studentEdit"   : "false"
            }
            docId = createDoc(self, data)

            host = mainHost + "/files"

            driverWB = webdriver.Chrome('.\chromedriver.exe')
            driverWB.get(host)

            ui_element = "input[id='name']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.send_keys(self.user.login_credentials["email"])

            ui_element = "input[id='password']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.send_keys(self.user.login_credentials["password"])
            
            ui_element = "input[id='submit-login']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            host = mainHost + "/files/file/" + docId + "/lool"
            driverWB.get(host)
            
            ui_element = "iframe"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.TAG_NAME, ui_element)))
            driverWB.switch_to.frame(element)
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.TAG_NAME, ui_element)))
            driverWB.switch_to.frame(element)
            time.sleep(self.timeToWaitShort)
            ui_element = "html/body"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.XPATH, ui_element)))
            element.send_keys("Der Loadtest der loaded den Test")
            time.sleep(self.timeToWaitShort)

            driverWB.quit()
            deleteDoc(self, docId)
       
    @tag('doc')
    @tag('sc')
    @task
    def newFilesXlsx(self):
        if "schueler" in str(self.user.login_credentials["email"]):
            pass
        else:
            mainHost = self.user.host
            data = {
                "name"          : "Loadtest xlsx",
                "type"          : "xlsx",
                "studentEdit"   : "false"
            }
            docId = createDoc(self, data)

            host = mainHost + "/files"

            driverWB = webdriver.Chrome('.\chromedriver.exe')
            driverWB.get(host)

            ui_element = "input[id='name']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.send_keys(self.user.login_credentials["email"])

            ui_element = "input[id='password']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.send_keys(self.user.login_credentials["password"])
            
            ui_element = "input[id='submit-login']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            host = mainHost + "/files/file/" + docId + "/lool"
            driverWB.get(host)
            
            ui_element = "iframe"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.TAG_NAME, ui_element)))
            driverWB.switch_to.frame(element)
            time.sleep(self.timeToWaitShort)
            ui_element = "input[id='formulaInput']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.send_keys("Der Loadtest der loaded den Test")
            ui_element = "td[id='tb_editbar_item_save']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            time.sleep(self.timeToWaitShort)

            driverWB.quit()
            deleteDoc(self, docId)

    @tag('doc')
    @tag('sc')        
    @task
    def newFilesPptx(self):
        if "schueler" in str(self.user.login_credentials["email"]):
            pass
        else:
            mainHost = self.user.host
            data = {
                "name"          : "Loadtest pptx",
                "type"          : "pptx",
                "studentEdit"   : "false"
            }
            docId = createDoc(self, data)

            host = mainHost + "/files"

            driverWB = webdriver.Chrome('.\chromedriver.exe')
            driverWB.get(host)

            ui_element = "input[id='name']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.send_keys(self.user.login_credentials["email"])

            ui_element = "input[id='password']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.send_keys(self.user.login_credentials["password"])
            
            ui_element = "input[id='submit-login']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            host = mainHost + "/files/file/" + docId + "/lool"
            driverWB.get(host)
            
            ui_element = "iframe"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.TAG_NAME, ui_element)))
            driverWB.switch_to.frame(element)
            ui_element = "iframe[class='resize-detector']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            driverWB.switch_to.frame(element)
            time.sleep(self.timeToWaitShort)
            ui_element = "html/body"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.XPATH, ui_element)))
            element.send_keys("Der Loadtest der loaded den Test")

            time.sleep(self.timeToWaitShort)

            driverWB.quit()
            
            deleteDoc(self, docId)

class AdminUser(HttpUser):
    weight = 1
    tasks = [WebsiteTasks]
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

class TeacherUser(HttpUser):
    weight = 3
    tasks = [WebsiteTasks]
    wait_time = between(5, 15)

    txn_id = ""
    user_type = "teacher"
    next_batch = ""
    filter_id = None
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

    txn_id = ""
    user_type = "pupil"
    next_batch = ""
    filter_id = None
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