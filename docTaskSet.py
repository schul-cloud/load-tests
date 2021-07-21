import time

from locustfile import PupilUser
from locust.user.task import TaskSet, task, tag
from selenium import webdriver
from selenium.common.exceptions import (ElementClickInterceptedException, NoSuchWindowException)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.by import By



class docTaskSet(TaskSet):

    def on_start(self):
        pass

    def on_stop(self):
        pass

    @tag('doc')
    @tag('sc')
    @task
    def newFilesXlsx(self):
        if isinstance(self._user, PupilUser):
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

            # Login User
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

            # Switch to editorframe
            ui_element = "iframe"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.TAG_NAME, ui_element)))
            driverWB.switch_to.frame(element)

            time.sleep(self.timeToWaitShort)

            # Edit Doc
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
        if isinstance(self._user, PupilUser):
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

            # Login User
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

            # Switch to editorframe
            ui_element = "iframe"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.TAG_NAME, ui_element)))
            driverWB.switch_to.frame(element)
            ui_element = "iframe[class='resize-detector']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            driverWB.switch_to.frame(element)

            time.sleep(self.timeToWaitShort)

            # Edit Doc
            ui_element = "html/body"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.XPATH, ui_element)))
            element.send_keys("Der Loadtest der loaded den Test")

            time.sleep(self.timeToWaitShort)

            driverWB.quit()

            deleteDoc(self, docId)

def createDoc(session, docdata):
    #Creates an doc at the Schulcloud website
    with session.client.request(
        "POST",
        "/files/newFile",
        headers = {
            # 'keep-alive' allows the connection to remain open for further requests/responses
            "Connection"        : "keep-alive",
            # Used for identifying Ajax requests
            "x-requested-with"  : "XMLHttpRequest",
            # Security token
            "csrf-token"        : session.csrf_token,
            # Data format for request body
            "Content-Type"      : "application/x-www-form-urlencoded",
            "Origin"            : session.user.host,
            # Indicates the origin of the request
            "Sec-Fetch-Site"    : "same-origin",
            # Indicates the mode of the request
            "Sec-Fetch-Mode"    : "cors",
            # Indicates the request's destination
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
    #Deletes an doc at the Schulcloud website
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