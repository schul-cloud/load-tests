import time
import os
import webbrowser
import hashlib

from locust import task, tag
from locust.user.task import TaskSet
from selenium import webdriver
from selenium.common.exceptions import (ElementClickInterceptedException, NoSuchWindowException)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0
from selenium.webdriver.common.by import By
 
class bbbTaskSet(TaskSet):
    bBBKey = os.environ.get("BBBKEY")
    host = os.environ.get("BBBHOST")
    numberRooms = 3
    numberUsers = 6
    timeToWaitShort = int(os.environ.get("TIMELONG"))
    timeToWaitLong = int(os.environ.get("TIMESHORT"))

    def on_start(self):
        pass

    def on_stop(self):
        pass

    @tag('bbb')
    @task
    def bBBTest(self):

        #Starts a chrome Browser
        driverWB = webdriver.Chrome('.\chromedriver.exe')
        driverWB.get(self.host)

        counterfirst = 0
        counterTab = 1
        while counterfirst < self.numberRooms:

            timestamp = str(time.time())
            # Creates a BBB-Room with a password
            v = "create"
            x = "meetingID=loadtest-" + timestamp + str(counterfirst) + "&name=loadtest-" + str(time.time()) + str(counterfirst) + "&moderatorPW=123&attendeePW=456&lockSettingsDisableMic=true"
            y = self.host + "/bigbluebutton/api/" + v + "?" + x
            z = str(v) + str(x) + str(self.bBBKey)
            w = str(y) + "&checksum=" + hashlib.sha1(z.encode()).hexdigest()

            driverWB.get(w)

            countersecond = 0

            # Moderator joins the room on a new Tab
            v = "join"
            x = "meetingID=loadtest-" + timestamp + str(counterfirst) + "&fullName=loadtest-" + str(counterfirst) + "userMLoadtest-" + str(countersecond) + "&userID=loadtest-" + str(counterfirst) + "userMLoadtest-" + str(countersecond) + "&password=123"
            y = self.host + "/bigbluebutton/api/" + v + "?" + x
            z = str(v) + str(x) + str(self.bBBKey)
            w = y + "&checksum=" + hashlib.sha1(z.encode()).hexdigest()

            windows = driverWB.window_handles
            driverWB.execute_script("window.open('');")
            driverWB.switch_to.window(driverWB.window_handles[counterTab])
            driverWB.get(w)
            # time.sleep(self.timeToWaitShort)

            # Chooses to join the room with "Listen only"
            ui_element = "i[class='icon--2q1XXw icon-bbb-listen']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            time.sleep(self.timeToWaitShort)

            # Clicks on the Plussign
            ui_element = "tippy-21"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.ID, ui_element)))
            element.click()

            # Clicks on the "Share external Video" button
            ui_element = "li[aria-labelledby='dropdown-item-label-26']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            # Inserts Videolink
            ui_element = "input[id='video-modal-input']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.send_keys('https://player.vimeo.com/video/418854539')

            time.sleep(self.timeToWaitShort)

            # Clicks on the button "Share a new video"
            ui_element = "button[class='button--Z2dosza md--Q7ug4 default--Z19H5du startBtn--ZifpQ9']"
            element = WebDriverWait(driverWB, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, ui_element)))
            element.click()

            time.sleep(self.timeToWaitLong)

            counterTab += 1
            countersecond += 1

            while countersecond < self.numberUsers:

                # Normal User joins the room
                v = "join"
                x = "meetingID=loadtest-" + timestamp + str(counterfirst) + "&fullName=loadtest-" + str(counterfirst) + "userLoadtest-" + str(countersecond) + "&userID=loadtest-" + str(counterfirst) + "userLoadtest-" + str(countersecond) + "&password=456"
                y = self.host + "/bigbluebutton/api/" + v + "?" + x
                z = str(v) + str(x) + str(self.bBBKey)
                w = y + "&checksum=" + hashlib.sha1(z.encode()).hexdigest()

                # changes the browsertab
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
        while counterfirst < self.numberRooms:
            # Closes all the rooms
            v = "end"
            x = "meetingID=loadtest-" + timestamp + str(counterfirst) + "&password=123"
            y = self.host + "/bigbluebutton/api/" + v + "?" + x
            z = str(v) + str(x) + str(self.bBBKey)
            w = str(y) + "&checksum=" + hashlib.sha1(z.encode()).hexdigest()

            driverWB.get(w)

            time.sleep(2)
            counterfirst += 1

        driverWB.quit()