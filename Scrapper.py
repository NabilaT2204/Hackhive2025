from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time

# Your login credentials
USERNAME = "100871157"
PASSWORD = "crashergames"

# Setup WebDriver (Ensure chromedriver is in your PATH)
service = Service("path/to/chromedriver")  # Update path to WebDriver
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Run in headless mode if you don't need UI
driver = webdriver.Chrome()

def build_urls(courses, term):
    base_url = "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/searchResults/searchResults"
    return [f"{base_url}?txt_subjectcoursecombo={course}&txt_term={term}" for course in courses]

courses = ["ALSU1101U", "APBS6600G", "AUTE3450U", "BIOL3650U", "BUSI2040U"]
term = "202501"
json_urls = build_urls(courses, term)

try:
    # Open login page
    driver.get("https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/registration/registerPostSignIn?mode=search&mepCode=UOIT")

    # Wait for login elements
    wait = WebDriverWait(driver, 10)
    
    username_field = driver.find_element(By.ID, "userNameInput")
    password_field = driver.find_element(By.ID, "passwordInput")
    buttons = driver.find_elements(By.TAG_NAME, "button")
    for btn in buttons:
        print(btn.text)


    #login_button = driver.find_element(By.XPATH, "//input[@value='Sign In']")

    # Enter login details
    username_field.send_keys(USERNAME)
    password_field.send_keys(PASSWORD)


    # Wait for the page to load after login
   
    login_button = wait.until(EC.element_to_be_clickable((By.ID, "submitButton")))
    #login_button.click()
    #time.sleep(5)  # Adjust as needed
    while True:
        try:
            if login_button.is_displayed():
                continue  # Button is still visible, wait
            else:
                break  # Button is gone, meaning the user clicked it
        except:
            break  # If the button element is no longer found, assume it's clicked

    # Get session cookies
    
    
    term_button = wait.until(EC.presence_of_element_located((By.ID, "term-go")))
    while True:
        try:
            if term_button.is_displayed():
                continue  # Button is still visible, wait
            else:
                break  # Button is gone, meaning the user clicked it
        except:
            break  # If the button element is no longer found, assume it's clicked

    cookies = driver.get_cookies()
    session_cookie = {cookie['name']: cookie['value'] for cookie in cookies}

    # Use session cookies to retrieve JSON data

  
    headers = {"User-Agent": "Mozilla/5.0"}
    

    # Print retrieved JSON data
    for url in json_urls:
        driver.get("https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/classSearch/classSearch")  # Refresh the page before each request
        
        response = requests.get(url, headers=headers, cookies=session_cookie)
        
        if response.status_code == 200:
            course_info = response.json().get("data", [])
            
            if course_info:
                print(f"Data found for URL: {course_info}")
                #course_info = response.json()["data"][0]
                #course_reference_number = course_info["courseReferenceNumber"]
                #display_name = course_info["faculty"][0]["displayName"]
                # Iterate over all meeting times
                #for meeting in course_info["meetingsFaculty"]:
                #    begin_time = meeting["meetingTime"]["beginTime"]
                #    end_time = meeting["meetingTime"]["endTime"]
                #    print(f"Course Reference Number: {course_reference_number}")
                #    print(f"Instructor: {display_name}")
                #    print(f"Begin Time: {begin_time}")
                #    print(f"End Time: {end_time}")
                print("----")
            else:
                print(f"No data found for URL: {url}")
        else:
            print(f"Failed to retrieve JSON from {url}. Status code: {response.status_code}")

finally:
    driver.quit()
