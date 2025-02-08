from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
import json
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
    
    count = 0
    # Print retrieved JSON data
    for url in json_urls:
        
        driver.get("https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/classSearch/classSearch")  # Refresh the page before each request
        
        response = requests.get(url, headers=headers, cookies=session_cookie)
        
        if response.status_code == 200:
            
            course_info = response.json()
            print(f"Retrieved data from URL: {url}")
            if course_info:
                with open(f"{courses[count]}.json", "w") as file:
                    json.dump(course_info, file, indent=4)
                print("----")
            else:
                print(f"No data found for URL: {url}")
        else:
            print(f"Failed to retrieve JSON from {url}. Status code: {response.status_code}")
        count += 1
finally:
    driver.quit()


# Load the JSON file
def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

def extract_meeting_info(data):
    extracted_data = []
    seen_crns = set()
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    for course in data.get("data", []):
        course_ref_num = course.get("courseReferenceNumber")
        if course_ref_num not in seen_crns:
            seen_crns.add(course_ref_num)
            for meeting in course.get("meetingsFaculty", []):
                meeting_time = meeting.get("meetingTime", {})
                active_days = [day.capitalize() for day in days_of_week if meeting_time.get(day, False)]
                
                extracted_data.append({
                    "courseReferenceNumber": course_ref_num,
                    "meetingScheduleType": meeting_time.get("meetingScheduleType"),
                    "beginTime": meeting_time.get("beginTime"),
                    "endTime": meeting_time.get("endTime"),
                    "hoursWeek": meeting_time.get("hoursWeek"),
                    "daysOfWeek": active_days
                })
    return extracted_data
def save_extracted_data(extracted_data, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(extracted_data, file, indent=4)

def extractdata(files):
    for course in files:
        data = load_json(f"{course}.json")
        extracted_data = extract_meeting_info(data)
        save_extracted_data(extracted_data, f"{course}.json")

extractdata(courses)




