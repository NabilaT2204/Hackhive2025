# pip install icalendar pytz
from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz
import json
import sys
import os
from pathlib import Path

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"[DEBUG] Created directory: {directory}")

def get_formatted_room(building, room):
    """Format room number based on building"""
    if building == "Shawenjigewining Hall":
        return f"SHA{room}"
    return room

def create_ics_from_json(json_data):
    print("[DEBUG] Creating ICS file from JSON data...")
    cal = Calendar()
    cal.add('prodid', '-//Schedule Converter//mxm.dk//')
    cal.add('version', '2.0')
    
    schedule_date = datetime.strptime(json_data['schedule_info']['generated_date'], '%Y-%m-%d %H:%M:%S')
    print(f"[DEBUG] Schedule generated date: {schedule_date}")
    
    timezone = pytz.timezone('America/Toronto')
    
    weekday_map = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
        'Thursday': 3, 'Friday': 4, 'Saturday': 5, 'Sunday': 6
    }
    
    for day, classes in json_data['weekly_schedule'].items():
        print(f"[DEBUG] Processing {day}'s schedule...")
        for class_info in classes:
            print(f"[DEBUG] Processing class: {class_info['course_code']}")
            event = Event()
            
            formatted_room = get_formatted_room(class_info['building'], class_info['room'])
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
            
            location = f"{class_info['building']} {formatted_room}, {class_info['campus']}"
            event.add('location', location)
            
            cal.add_component(event)
    
    return cal

def process_json_files(schedule_dir):
    """Process all JSON files in the specified directory"""
    for json_file in schedule_dir.glob('generated_schedule.json'):
        try:
            print(f"[DEBUG] Processing {json_file.name}...")
            with open(json_file, 'r') as f:
                schedule_data = json.load(f)
            
            calendar = create_ics_from_json(schedule_data)
            
            # Create output filename by replacing .json with .ics
            output_filename = 'schedule.ics'
            output_path = schedule_dir / output_filename
            
            print(f"[DEBUG] Saving calendar to {output_path}")
            with open(output_path, 'wb') as f:
                f.write(calendar.to_ical())
            print(f"[DEBUG] Successfully created {output_filename}")
            
        except Exception as e:
            print(f"[ERROR] Failed to process {json_file.name}: {str(e)}")

def main():
    try:
        print("[DEBUG] Starting main process...")
        
        # Get the directory where the script is located
        script_dir = Path(__file__).parent
        schedule_dir = script_dir / "Schedule Jsons"
        
        # Ensure the Schedule Jsons directory exists
        ensure_directory_exists(schedule_dir)
        
        # Check if there are any JSON files to process
        json_files = list(schedule_dir.glob('generated_schedule.json'))
        if not json_files:
            print("[ERROR] No JSON files found in 'Schedule Jsons' directory")
            sys.exit(1)
            
        # Process all JSON files in the directory
        process_json_files(schedule_dir)
        print("[DEBUG] All files processed successfully!")
        
    except Exception as e:
        print(f"[ERROR] An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
