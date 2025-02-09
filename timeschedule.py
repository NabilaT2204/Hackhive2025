from itertools import product
from datetime import datetime, timedelta

class TimePreference:
    def __init__(self, day, earliest_time="0000", latest_time="2359"):
        self.day = day
        self.earliest_time = earliest_time
        self.latest_time = latest_time

def parse_time(time_str):
    """Convert time string (e.g., '1440') to datetime object"""
    return datetime.strptime(time_str, '%H%M')

def check_time_conflict(slot1, slot2):
    """Check if two time slots conflict"""
    start1 = parse_time(slot1['beginTime'])
    end1 = parse_time(slot1['endTime'])
    start2 = parse_time(slot2['beginTime'])
    end2 = parse_time(slot2['endTime'])
    
    if not set(slot1['daysOfWeek']).intersection(set(slot2['daysOfWeek'])):
        return False
    
    return not (end1 <= start2 or end2 <= start1)

def is_within_time_preferences(section, time_preferences):
    """Check if a section falls within the preferred time ranges"""
    for day in section['daysOfWeek']:
        day_prefs = [pref for pref in time_preferences if pref.day == day]
        if not day_prefs:  # No preferences for this day, assume it's okay
            continue
            
        for pref in day_prefs:
            start_time = parse_time(section['beginTime'])
            end_time = parse_time(section['endTime'])
            earliest = parse_time(pref.earliest_time)
            latest = parse_time(pref.latest_time)
            
            if start_time < earliest or end_time > latest:
                return False
    return True

def get_required_meeting_types(course_sections):
    """Get all meeting types required for a course"""
    return set(section['meetingScheduleType'] for section in course_sections)

def find_best_schedule(courses_data, time_preferences=None):
    """
    Find the best possible schedule that includes one of each required meeting type per course
    and fits within the specified time preferences
    """
    if time_preferences is None:
        time_preferences = []
    
    # Group sections by meeting type for each course
    course_sections_by_type = {}
    for course_code, sections in courses_data.items():
        course_sections_by_type[course_code] = {}
        for section in sections:
            # Skip sections that don't fit time preferences
            if time_preferences and not is_within_time_preferences(section, time_preferences):
                continue
                
            meeting_type = section['meetingScheduleType']
            if meeting_type not in course_sections_by_type[course_code]:
                course_sections_by_type[course_code][meeting_type] = []
            course_sections_by_type[course_code][meeting_type].append(section)
    
    # Generate all possible combinations of sections for each course
    course_combinations = {}
    for course_code, sections_by_type in course_sections_by_type.items():
        required_types = get_required_meeting_types(courses_data[course_code])
        type_combinations = []
        
        sections_by_required_type = [sections_by_type.get(req_type, []) for req_type in required_types]
        
        # Check if any required type has no valid sections
        if any(not sections for sections in sections_by_required_type):
            print(f"Warning: No valid sections found for some required types in {course_code}")
            continue
        
        for combination in product(*sections_by_required_type):
            has_conflict = False
            for i in range(len(combination)):
                for j in range(i + 1, len(combination)):
                    if check_time_conflict(combination[i], combination[j]):
                        has_conflict = True
                        break
                if has_conflict:
                    break
            
            if not has_conflict:
                type_combinations.append(combination)
        
        course_combinations[course_code] = type_combinations
    
    # Check if any course has no valid combinations
    if not all(course_combinations.values()):
        return None
    
    # Generate all possible schedule combinations
    best_schedule = None
    min_gaps = float('inf')
    
    for schedule_combination in product(*course_combinations.values()):
        schedule = [section for course_sections in schedule_combination for section in course_sections]
        
        has_conflict = False
        for i in range(len(schedule)):
            for j in range(i + 1, len(schedule)):
                if check_time_conflict(schedule[i], schedule[j]):
                    has_conflict = True
                    break
            if has_conflict:
                break
        
        if not has_conflict:
            total_gaps = calculate_schedule_gaps(schedule)
            
            if total_gaps < min_gaps:
                min_gaps = total_gaps
                best_schedule = schedule
    
    return best_schedule

def calculate_schedule_gaps(schedule):
    """Calculate total gaps between classes in minutes"""
    total_gaps = 0
    
    classes_by_day = {}
    for section in schedule:
        for day in section['daysOfWeek']:
            if day not in classes_by_day:
                classes_by_day[day] = []
            classes_by_day[day].append(section)
    
    for day, classes in classes_by_day.items():
        sorted_classes = sorted(classes, key=lambda x: parse_time(x['beginTime']))
        
        for i in range(len(sorted_classes) - 1):
            current_end = parse_time(sorted_classes[i]['endTime'])
            next_start = parse_time(sorted_classes[i + 1]['beginTime'])
            gap = (next_start - current_end).seconds / 60
            if gap > 20:  # Only count gaps longer than 20 minutes
                total_gaps += gap
    
    return total_gaps

def format_schedule(schedule, courses_data):
    """Format the schedule in a readable way"""
    if not schedule:
        return "No valid schedule found that meets the specified time preferences!"
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    formatted_schedule = []
    
    for day in days_order:
        day_classes = [s for s in schedule if day in s['daysOfWeek']]
        if day_classes:
            formatted_schedule.append(f"\n{day}:")
            sorted_classes = sorted(day_classes, key=lambda x: parse_time(x['beginTime']))
            
            for class_info in sorted_classes:
                course_code = next(code for code, sections in courses_data.items() if class_info in sections)
                formatted_schedule.append(
                    f"  {course_code} - {class_info['meetingScheduleType']}: "
                    f"{class_info['beginTime'][:2]}:{class_info['beginTime'][2:]} - "
                    f"{class_info['endTime'][:2]}:{class_info['endTime'][2:]} - "
                    f"CRN: {class_info['courseReferenceNumber']}"
                )
    
    return "\n".join(formatted_schedule)
def format_schedule_to_json(schedule, courses_data):
    """Format the schedule as a JSON structure"""
    if not schedule:
        return {
            "success": False,
            "message": "No valid schedule found that meets the specified time preferences!",
            "schedule": None
        }
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    schedule_json = {
        "success": True,
        "message": "Schedule successfully generated",
        "schedule": {
            "days": []
        }
    }
    
    for day in days_order:
        day_classes = [s for s in schedule if day in s['daysOfWeek']]
        if day_classes:
            day_data = {
                "dayName": day,
                "classes": []
            }
            
            sorted_classes = sorted(day_classes, key=lambda x: parse_time(x['beginTime']))
            
            for class_info in sorted_classes:
                course_code = next(code for code, sections in courses_data.items() 
                                 if class_info in sections)
                class_data = {
                    "courseCode": course_code,
                    "meetingType": class_info['meetingScheduleType'],
                    "startTime": f"{class_info['beginTime'][:2]}:{class_info['beginTime'][2:]}",
                    "endTime": f"{class_info['endTime'][:2]}:{class_info['endTime'][2:]}",
                    "crn": class_info['courseReferenceNumber']
                }
                day_data["classes"].append(class_data)
            
            schedule_json["schedule"]["days"].append(day_data)
    
    return schedule_json

# Example usage
if __name__ == "__main__":
    import json
    
    # Load course data
    with open('combined_courses.json', 'r') as file:
        courses_data = json.load(file)
    
    # Example time preferences
    time_preferences = [
        TimePreference("Monday", "1000", "1700"),
        TimePreference("Friday", "0800", "1700"),
        TimePreference("Tuesday", "0800", "1700"),
        TimePreference("Wednesday", "0800", "1700"),
        TimePreference("Thursday", "0800", "1700"),
    ]
    
    best_schedule = find_best_schedule(courses_data, time_preferences)
    schedule_json = format_schedule_to_json(best_schedule, courses_data)
    
    # Output the JSON
    print(json.dumps(schedule_json, indent=2))
    
    # Optionally save to file
    with open('schedule_output.json', 'w') as f:
        json.dump(schedule_json, f, indent=2)
