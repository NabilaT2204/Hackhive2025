from datetime import datetime, timedelta
from icalendar import Calendar, Event
import pytz
import json
import sys
from pathlib import Path

def create_ics_from_json(json_data):
    # Create calendar with minimal required properties
    cal = Calendar()
    cal.add('prodid', '-//Test Calendar//EN')
    cal.add('version', '2.0')
    cal.add('calscale', 'GREGORIAN')

    # Set timezone
    tz = pytz.timezone('America/Toronto')

    # Get the schedule start date (next Monday)
    schedule_date = datetime.strptime(json_data['schedule_info']['generated_date'], '%Y-%m-%d %H:%M:%S')
    start_date = schedule_date.date()
    while start_date.weekday() != 0:  # 0 is Monday
        start_date += timedelta(days=1)

    # Process each week's schedule for 12 weeks
    weekday_map = {
        'Monday': 0, 'Tuesday': 1, 'Wednesday': 2,
        'Thursday': 3, 'Friday': 4
    }

    for week in range(12):  # Repeat for 12 weeks
        week_start_date = start_date + timedelta(weeks=week)

        for day, classes in json_data['weekly_schedule'].items():
            if not classes:  # Skip empty days
                continue

            # Calculate the date for this day's classes in the current week
            day_offset = weekday_map[day]
            class_date = week_start_date + timedelta(days=day_offset)

            # Process each class
            for class_info in classes:
                event = Event()

                # Parse times
                start_time = datetime.strptime(class_info['start_time'], '%I:%M %p').time()
                end_time = datetime.strptime(class_info['end_time'], '%I:%M %p').time()

                # Create event start and end times
                start = tz.localize(datetime.combine(class_date, start_time))
                end = tz.localize(datetime.combine(class_date, end_time))

                # Add basic event details
                event.add('summary', f"{class_info['course_code']} {class_info['type']}")
                event.add('dtstart', start)
                event.add('dtend', end)
                event.add('location', f"{class_info['building']} {class_info['room']}")

                # Add to calendar
                cal.add_component(event)

    return cal

def main():
    try:
        # Get script directory
        script_dir = Path(__file__).parent
        schedule_dir = script_dir / "Schedule Jsons"
        
        # Create directory if it doesn't exist
        schedule_dir.mkdir(exist_ok=True)
        
        # Find and process JSON file
        json_file = schedule_dir / 'generated_schedule.json'
        if not json_file.exists():
            print("Error: generated_schedule.json not found")
            sys.exit(1)
        
        # Read and process JSON
        with open(json_file, 'r', encoding='utf-8') as f:
            schedule_data = json.load(f)
        
        # Create calendar
        calendar = create_ics_from_json(schedule_data)
        
        # Save ICS file
        output_path = schedule_dir / 'schedule.ics'
        with open(output_path, 'wb') as f:
            f.write(calendar.to_ical())
        
        print(f"Calendar created successfully at {output_path}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
