from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import time
import json
import os
import sys

# Get courses from command line or use default list
courses = sys.argv[1:] if len(sys.argv) > 1 else ["MATH1010U", "CSCI2050U", "BUSI1700U", "PHY1020U", "CSCI1061U"]

def build_urls(courses, term):
    base_url = "https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/searchResults/searchResults"
    return [f"{base_url}?txt_subjectcoursecombo={course}&txt_term={term}" for course in courses]

def scrape_course_data(driver, url, session_cookie, headers):
    driver.get("https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/classSearch/classSearch")
    response = requests.get(url, headers=headers, cookies=session_cookie)
    if response.status_code == 200:
        return response.json()
    return None

def extract_meeting_info(data):
    extracted_data = []
    seen_crns = set()
    days_of_week = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    for course in data.get("data", []):
        course_ref_num = course.get("courseReferenceNumber")
        if course_ref_num not in seen_crns:
            seen_crns.add(course_ref_num)
            display_names = [faculty.get("displayName") for faculty in course.get("faculty", []) if faculty.get("displayName")]

            for meeting in course.get("meetingsFaculty", []):
                meeting_time = meeting.get("meetingTime", {})
                active_days = [day.capitalize() for day in days_of_week if meeting_time.get(day, False)]
                
                extracted_data.append({
                    "displayName": ", ".join(display_names) if display_names else "N/A",
                    "startdate": meeting_time.get("startDate"),
                    "building": meeting_time.get("buildingDescription"),
                    "enddate": meeting_time.get("endDate"),
                    "campus": meeting_time.get("campusDescription"),
                    "room":  meeting_time.get("room"),
                    "courseReferenceNumber": course_ref_num,
                    "meetingScheduleType": meeting_time.get("meetingScheduleType"),
                    "beginTime": meeting_time.get("beginTime"),
                    "endTime": meeting_time.get("endTime"),
                    "hoursWeek": meeting_time.get("hoursWeek"),
                    "daysOfWeek": active_days
                })
    
    return extracted_data

def save_course_data(course_code, data):
    """Save individual course data to a JSON file"""
    with open(f"{course_code}.json", "w") as f:
        json.dump(data, f, indent=4)
    print(f"Saved data for {course_code}")

def save_combined_data(combined_data):
    """Save the combined course data to a single JSON file"""
    with open("combined_courses.json", "w") as f:
        json.dump(combined_data, f, indent=4)
    print("Saved combined course data")

def cleanup_individual_files(courses):
    """Remove individual course JSON files"""
    for course in courses:
        try:
            os.remove(f"{course}.json")
            print(f"Removed {course}.json")
        except FileNotFoundError:
            print(f"Warning: {course}.json not found")

def main():
    print("Starting course data scraping...")
    term = "202501"
    json_urls = build_urls(courses, term)
    
    # Setup WebDriver
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 10)
    
    try:
        # Open login page and wait for manual login
        print("Opening browser for manual login...")
        driver.get("https://ssp.mycampus.ca/StudentRegistrationSsb/ssb/registration/registerPostSignIn?mode=search&mepCode=UOIT")
        
        term_button = wait.until(EC.presence_of_element_located((By.ID, "term-go")))
        while True:
            try:
                if term_button.is_displayed():
                    continue  # Button is still visible, wait
                else:
                    break  # Button is gone, meaning the user clicked it
            except:
                break  # If the button element is no longer found, assume it's clicked
        
        # Get session cookies after manual login
        cookies = driver.get_cookies()
        session_cookie = {cookie['name']: cookie['value'] for cookie in cookies}
        headers = {"User-Agent": "Mozilla/5.0"}
        
        # Process each course
        combined_data = {}
        for i, url in enumerate(json_urls):
            course_code = courses[i]
            print(f"\nProcessing {course_code}...")
            
            # Scrape and extract data
            course_data = scrape_course_data(driver, url, session_cookie, headers)
            if course_data:
                extracted_data = extract_meeting_info(course_data)
                combined_data[course_code] = extracted_data
                
                # Save individual file
                save_course_data(course_code, extracted_data)
            else:
                print(f"Failed to retrieve data for {course_code}")
        
        # Save combined data
        print("\nSaving combined data...")
        save_combined_data(combined_data)
        
        # Cleanup individual files
        print("\nCleaning up individual files...")
        cleanup_individual_files(courses)
        
        print("\nProcess completed successfully!")
        driver.quit()
        return
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        print("Browser closed")

if __name__ == "__main__":
    main()
