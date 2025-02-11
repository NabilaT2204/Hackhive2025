from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import requests
import time
import json
import os
import sys
from datetime import datetime
import traceback

# Get courses from command line or use default list
courses = sys.argv[1:] if len(sys.argv) > 1 else ["MATH1010U", "CSCI2050U", "BUSI1700U", "PHY1020U", "CSCI1061U"]

def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = ["logs", "logs/Scrapper Logs", "Schedule Jsons"]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

def log_error(error_message, traceback_info=None):
    """Log error to a timestamped file in the logs directory"""
    ensure_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/Scrapper Logs/Scrapper_logs_{timestamp}.txt"
    
    with open(filename, "w") as f:
        f.write(f"Error occurred at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Error message: {error_message}\n")
        if traceback_info:
            f.write("\nTraceback:\n")
            f.write(traceback_info)
    
    print(f"Error logged to: {filename}")

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
    """Save individual course data to a JSON file in Schedule Jsons directory"""
    try:
        ensure_directories()
        filepath = os.path.join("Schedule Jsons", f"{course_code}.json")
        with open(filepath, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Saved data for {course_code}")
    except Exception as e:
        log_error(f"Error saving data for {course_code}: {str(e)}", traceback.format_exc())
        raise

def save_combined_data(combined_data):
    """Save the combined course data to a single JSON file in Schedule Jsons directory"""
    try:
        ensure_directories()
        filepath = os.path.join("Schedule Jsons", "combined_courses.json")
        with open(filepath, "w") as f:
            json.dump(combined_data, f, indent=4)
        print("Saved combined course data")
    except Exception as e:
        log_error(f"Error saving combined data: {str(e)}", traceback.format_exc())
        raise

def cleanup_individual_files(courses):
    """Remove individual course JSON files from Schedule Jsons directory"""
    for course in courses:
        try:
            filepath = os.path.join("Schedule Jsons", f"{course}.json")
            os.remove(filepath)
            print(f"Removed {course}.json")
        except FileNotFoundError:
            print(f"Warning: {course}.json not found")
        except Exception as e:
            log_error(f"Error removing {course}.json: {str(e)}", traceback.format_exc())

def main():
    print("Starting course data scraping...")
    term = "202501"
    json_urls = build_urls(courses, term)
    driver = None
    
    try:
        # Setup Chrome options for controlled window size
        chrome_options = Options()
        chrome_options.add_argument("--app=data:,")  # Run in app mode
        chrome_options.add_argument("--window-size=1024,768")
        chrome_options.add_argument("--window-position=0,0")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-extensions")
        # Add these new options to disable password saving prompts
        chrome_options.add_argument("--password-store=basic")
        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        # Setup WebDriver with custom options
        driver = webdriver.Chrome(options=chrome_options)
        
        # Set window size after browser opens to ensure it takes effect
        driver.set_window_size(1024, 768)
        driver.set_window_position(0, 0)
        
        wait = WebDriverWait(driver, 1000000)
        
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
            
            try:
                # Scrape and extract data
                course_data = scrape_course_data(driver, url, session_cookie, headers)
                if course_data:
                    extracted_data = extract_meeting_info(course_data)
                    combined_data[course_code] = extracted_data
                    
                    # Save individual file
                    save_course_data(course_code, extracted_data)
                else:
                    error_msg = f"Failed to retrieve data for {course_code}"
                    print(error_msg)
                    log_error(error_msg)
            except Exception as e:
                log_error(f"Error processing {course_code}: {str(e)}", traceback.format_exc())
                continue
        
        # Save combined data
        print("\nSaving combined data...")
        save_combined_data(combined_data)
        
        # Cleanup individual files
        print("\nCleaning up individual files...")
        cleanup_individual_files(courses)
        
        print("\nProcess completed successfully!")
        
    except Exception as e:
        error_msg = f"An error occurred: {str(e)}"
        print(error_msg)
        log_error(error_msg, traceback.format_exc())
    finally:
        if driver:
            driver.quit()
        print("Browser closed")

if __name__ == "__main__":
    main()
