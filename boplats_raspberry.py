#!/usr/bin/env python3
import pycurl
import certifi
import re
import json
import time
import smtplib
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from io import BytesIO
from urllib.parse import urlencode

## Search for apartments with given parameters and save result as html
buffer = BytesIO()
with open('out.html', 'wb') as f:
	c = pycurl.Curl()
	c.setopt(c.URL, 'https://nya.boplats.se/sok')
	post_data = {
		"itemtype":"1hand",
		"rent":"7000",
		"city":"508A8CB406FE001F00030A60",
		"rooms":"3",
		"area":"508A8CB4057B00660003286F",
		"area-508A8CB4029C003F0003E4C0":"on",
		"area-508A8CB405870072000312A3":"on",
		"area-508A8CB40294003E0003C757":"on",
		"area-508A8CB4057B00660003286F":"on",
		"508A8CB406FE001F00030A60":"508A8CB4057B00660003286F",
		"508A8CB406FE001F00030A60-508A8CB4029C003F0003E4C0":"on",
		"508A8CB406FE001F00030A60-508A8CB405870072000312A3":"on",
		"508A8CB406FE001F00030A60-508A8CB40294003E0003C757":"on",
		"508A8CB406FE001F00030A60-508A8CB4057B00660003286F":"on",
		"508A8CB4FCA4001400031899":"alla",
		"508A8CB400A1001800031575":"alla",
		"54B00286892C0009000349A6":"alla",
		"508A8CB4044A002300035C4C":"alla",
		"53EC5D3E25A7000A0003704B":"alla",
		"508A8CB405A30025000303BA":"alla",
		"508A8CB406840026000312AF":"alla",
		"508A8CB4F981002B000339E4":"alla",
		"508A8CB4FBDC002E000345E7":"alla",
		"508A8CB4FD6E00300003D3DD":"alla",
		"5163DE62FA20000700035F18":"alla",
		"squaremeters":"60",
		"objecttype":"newProduction",
		"objecttype-normal":"on",
		"objecttype-newProduction":"on",
		"moreoptionsvisible":"true",
		"moveindate":"any",
		"deposit":"",
		"objectproperties":"",
		"sortorder":"startPublishTime-descending",
		"listtype":"imagelist"
	}
	postfields = urlencode(post_data)
	c.setopt(c.POSTFIELDS, postfields)
	c.setopt(c.CAINFO, certifi.where())
	c.setopt(c.WRITEDATA, f)
	c.perform()
	c.close()
	
## Parse the html file and save links to all apartments
soup = BeautifulSoup(open("out.html"), "html.parser")
allLinks = []
for link in soup.findAll('a'):
    allLinks.append(link.get('href'))

availableApartments = []
i = 0
while i < len(allLinks):
	if "/1hand/" in allLinks[i]:
		availableApartments.append(allLinks[i])
	i += 1
    
## Sign in and save cookie to be able to apply
## Must be done once every 20 minutes
display = Display(visible=0, size=(800,600))
display.start()
driver = webdriver.Firefox(executable_path=r"/usr/local/bin/geckodriver")
driver.get('https://nya.boplats.se/login/')
driver.switch_to.frame(0);
driver.find_element_by_id("username").send_keys('<USERNAME>')
driver.find_element_by_id("password").send_keys('<PASSWORD>')
driver.find_element_by_name('login_button').click()

cookies_dict = {}
cookies_dict = driver.get_cookies()
cookieValue = cookies_dict[0]['value']
httpHeader = 'Cookie: Boplats-session=' + cookieValue
driver.close()
display.stop()
time(5)
driver.quit()

## Find all apartments previously applied to
with open('applied.html', 'wb') as f:
	c = pycurl.Curl()
	c.setopt(c.URL, 'https://nya.boplats.se/minsida/ansokta')	
	c.setopt(c.HTTPHEADER, [httpHeader])
	c.setopt(c.CAINFO, certifi.where())
	c.setopt(c.WRITEDATA, f)
	c.perform()
	c.close()
	
apartmentsApplied = []
soup = BeautifulSoup(open("applied.html"), "html.parser")
data = soup.findAll('table',attrs={'class':'ansokta applications'})
for table in data:
    links = table.findAll('a')
for a in links:
	if len(a.get('href')) > 1:
		apartmentsApplied.append(a.get('href'))

buffer = BytesIO()
## Apply to each apartment
for apartment in availableApartments:
	if apartment not in apartmentsApplied:
		c = pycurl.Curl()
		c.setopt(c.URL, apartment)
		c.setopt(c.HTTPHEADER, [httpHeader])
		post_data = {'apply':'apply'}
		postfields = urlencode(post_data)
		c.setopt(c.POSTFIELDS, postfields)
		c.setopt(c.CAINFO, certifi.where())
		c.setopt(c.WRITEDATA, buffer)
		c.perform()
		c.close()

## Send email and alert me of all apartments I've applied to
newlyAppliedApartments = []
for apartment in availableApartments:
	if apartment not in apartmentsApplied:
		newlyAppliedApartments.append(apartment)

if len(newlyAppliedApartments) != 0:
	mailFrom = "<MAIL FROM>"
	mailTo = "<MAIL TO>"
	subject = "Applied on Boplats"
	text = "\n".join(newlyAppliedApartments)
	message = 'Subject: {}\n\n{}'.format(subject, text)
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.starttls()
	server.login("<USERID>", "<PASSWORD>")
	server.sendmail(mailFrom, mailTo, message)
	server.quit()
