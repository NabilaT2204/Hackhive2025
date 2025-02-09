# pip install icalendar pytz ollama requests
import subprocess
import time
import json
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz
from ollama import Client
import sys
import platform
import requests

class OllamaManager:
    def __init__(self):
        self.ollama_process = None
        self.system = platform.system()
        print(f"[DEBUG] Detected OS: {self.system}")
        
    def get_ollama_path(self):
        if self.system == "Windows":
            return "ollama.exe"
        return "ollama"
        
    def is_ollama_running(self):
        try:
            requests.get("http://localhost:11434/api/version")
            print("[DEBUG] Ollama service is running.")
            return True
        except requests.exceptions.ConnectionError:
            print("[DEBUG] Ollama service is not running.")
            return False
            
    def start_ollama(self):
        if not self.is_ollama_running():
            print("[DEBUG] Starting Ollama service...")
            if self.system == "Windows":
                self.ollama_process = subprocess.Popen(
                    [self.get_ollama_path()],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                self.ollama_process = subprocess.Popen(
                    [self.get_ollama_path()],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            
            # Wait for Ollama to start
            max_attempts = 30
            attempts = 0
            while attempts < max_attempts:
                if self.is_ollama_running():
                    print("[DEBUG] Ollama service started successfully!")
                    break
                time.sleep(1)
                attempts += 1
            else:
                raise Exception("[ERROR] Failed to start Ollama service")

    def ensure_model_installed(self, model_name):
        try:
            print(f"[DEBUG] Checking if model {model_name} is installed...")
            response = requests.get("http://localhost:11434/api/tags")
            models = response.json().get("models", [])
            model_exists = any(model["name"] == model_name for model in models)
            
            if not model_exists:
                print(f"[DEBUG] Installing {model_name} model...")
                subprocess.run([self.get_ollama_path(), "pull", model_name])
                print(f"[DEBUG] Model {model_name} installed successfully!")
        except Exception as e:
            print(f"[ERROR] Error checking/installing model: {str(e)}")
            print("[DEBUG] Attempting to pull model anyway...")
            subprocess.run([self.get_ollama_path(), "pull", model_name])

    def stop_ollama(self):
        if self.ollama_process:
            self.ollama_process.terminate()
            self.ollama_process.wait()
            print("[DEBUG] Ollama service stopped.")

def get_formatted_room(building, room):
    """Format room number based on building"""
    if building == "Shawenjigewining Hall":
        return f"SHA{room}"
    return room

def create_ics_from_json(json_data, ollama_manager):
    print("[DEBUG] Creating ICS file from JSON data...")
    cal = Calendar()
    cal.add('prodid', '-//Schedule Converter//mxm.dk//')
    cal.add('version', '2.0')
    
    schedule_date = datetime.strptime(json_data['schedule_info']['generated_date'], '%Y-%m-%d %H:%M:%S')
    print(f"[DEBUG] Schedule generated date: {schedule_date}")
    
    timezone = pytz.timezone('America/Toronto')
    
    weekday_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
                   'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6}
    
    client = Client(host='http://localhost:11434')
    for day, classes in json_data['weekly_schedule'].items():
        print(f"[DEBUG] Processing {day}'s schedule...")
        for class_info in classes:
            print(f"[DEBUG] Processing class: {class_info['course_code']}")
            event = Event()
            
            # Format room number based on building
            formatted_room = get_formatted_room(class_info['building'], class_info['room'])
            
            # Create description from location information
            description = f"Campus: {class_info['campus']}\nBuilding: {class_info['building']}\nRoom: {formatted_room}"
            
            event.add('summary', f"{class_info['course_code']} - {class_info['type']}")
            event.add('description', description)
            
            today = schedule_date.date()
            days_ahead = weekday_map[day] - today.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_day = today + timedelta(days=days_ahead)
            
            start_time = datetime.strptime(class_info['start_time'], '%I:%M %p').time()
            end_time = datetime.strptime(class_info['end_time'], '%I:%M %p').time()
            
            start_datetime = timezone.localize(datetime.combine(next_day, start_time))
            end_datetime = timezone.localize(datetime.combine(next_day, end_time))
            
            print(f"[DEBUG] Event start: {start_datetime}, end: {end_datetime}")
            
            event.add('dtstart', start_datetime)
            event.add('dtend', end_datetime)
            event.add('rrule', {'freq': 'weekly', 'count': 12})
            
            # Use formatted room in location as well
            location = f"{class_info['building']} {formatted_room}, {class_info['campus']}"
            event.add('location', location)
            
            cal.add_component(event)
    
    return cal

def save_calendar(calendar, filename='schedule.ics'):
    print(f"[DEBUG] Saving calendar to {filename}...")
    with open(filename, 'wb') as f:
        f.write(calendar.to_ical())
    print("[DEBUG] Calendar file saved successfully!")

def main():
    try:
        print("[DEBUG] Starting main process...")
        ollama_manager = OllamaManager()
        ollama_manager.start_ollama()
        ollama_manager.ensure_model_installed('deepseek-r1:1.5b')
        
        with open('generated_schedule.json', 'r') as f:
            schedule_data = json.load(f)
        
        print("[DEBUG] JSON data loaded successfully.")
        calendar = create_ics_from_json(schedule_data, ollama_manager)
        save_calendar(calendar)
        print("[DEBUG] Calendar file has been created successfully!")
        
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        sys.exit(1)
        
    finally:
        ollama_manager.stop_ollama()

if __name__ == "__main__":
    main()
