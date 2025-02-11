import json
from datetime import datetime
from collections import defaultdict
import os
import traceback

def ensure_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        os.path.join("logs", "Algorithm Logs"),
        "Schedule Jsons"
    ]
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)

def log_error(error_message, traceback_info=None):
    """Log error to a timestamped file in the logs/Algorithm Logs directory"""
    ensure_directories()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join("logs", "Algorithm Logs", f"Algorithm_logs_{timestamp}.txt")
    
    with open(filename, "w") as f:
        f.write(f"Error occurred at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 50 + "\n")
        f.write(f"Error message: {error_message}\n")
        if traceback_info:
            f.write("\nTraceback:\n")
            f.write(traceback_info)
    
    print(f"Error logged to: {filename}")

class TimePreference:
    def __init__(self, restrictions=None):
        # If no restrictions are provided, it defaults to the entire week being unrestricted
        if restrictions is None:
            restrictions = {
                'Monday': {'earliest': '0000', 'latest': '2359'},
                'Tuesday': {'earliest': '0000', 'latest': '2359'},
                'Wednesday': {'earliest': '0000', 'latest': '2359'},
                'Thursday': {'earliest': '0000', 'latest': '2359'},
                'Friday': {'earliest': '0000', 'latest': '2359'}
            }
        self.restrictions = restrictions
    
    def set_restriction(self, day, earliest=None, latest=None):
        """Set time restrictions for a specific day."""
        if earliest:
            self.restrictions[day]['earliest'] = earliest
        if latest:
            self.restrictions[day]['latest'] = latest
    
    def is_time_allowed(self, session):
        """Check if a session falls within allowed time frames."""
        session_start = session['beginTime']
        session_end = session['endTime']
        
        for day in session['daysOfWeek']:
            day_restrictions = self.restrictions[day]
            if (session_start < day_restrictions['earliest'] or 
                session_end > day_restrictions['latest']):
                return False
        return True

def validate_schedule_possibility(course_data, time_preferences=None):
    """
    Validate that at least one section of each required component (LEC, LAB, TUT) 
    is available within the time preferences for each course.
    Returns (is_valid, error_list)
    """
    error_list = []  # Changed from error_messages
    
    for course_code, sessions in course_data.items():
        required_types = get_required_session_types(sessions)
        available_types = defaultdict(bool)
        
        for session in sessions:
            session_type = session['meetingScheduleType']
            if required_types[session_type]:
                if not time_preferences or time_preferences.is_time_allowed(session):
                    available_types[session_type] = True
        
        missing_types = []
        for session_type, required in required_types.items():
            if required and not available_types[session_type]:
                missing_types.append(session_type)
        
        if missing_types:
            error_list.append({  # Structured error format
                "course": course_code,
                "missing_types": missing_types,
                "message": f"Course {course_code} has no available {', '.join(missing_types)} sections within the specified time preferences."
            })
    
    is_valid = len(error_list) == 0
    return is_valid, error_list  # Now returns list instead of string

def log_validity_errors(errors):
    """Log validation errors to validity.json"""
    ensure_directories()
    validity_path = os.path.join("validation", "validity.json")
    
    error_data = {
        "validation_errors": errors  # Directly use the structured list
    }
    
    with open(validity_path, 'w') as f:
        json.dump(error_data, f, indent=2)
    
    print(f"Validation issues logged to: {validity_path}")

def convert_time_to_minutes(time_str):
    """Convert time string (e.g., '0940') to minutes since midnight."""
    hours = int(time_str[:2])
    minutes = int(time_str[2:])
    return hours * 60 + minutes

def check_time_conflict(session1, session2):
    """Check if two sessions have a time conflict."""
    s1_start = convert_time_to_minutes(session1['beginTime'])
    s1_end = convert_time_to_minutes(session1['endTime'])
    s2_start = convert_time_to_minutes(session2['beginTime'])
    s2_end = convert_time_to_minutes(session2['endTime'])
    
    common_days = set(session1['daysOfWeek']) & set(session2['daysOfWeek'])
    if not common_days:
        return False
    
    return not (s1_end <= s2_start or s2_end <= s1_start)

def calculate_time_gap(session1, session2):
    """Calculate the time gap between two sessions in minutes."""
    if not set(session1['daysOfWeek']) & set(session2['daysOfWeek']):
        return float('inf')
    
    s1_end = convert_time_to_minutes(session1['endTime'])
    s2_start = convert_time_to_minutes(session2['beginTime'])
    
    return abs(s2_start - s1_end)

def calculate_schedule_score(sessions):
    """Calculate a score for the schedule based on time gaps and day distribution."""
    if not sessions:
        return 0
    
    # Initialize day counts
    day_counts = defaultdict(int)
    for session in sessions:
        for day in session['daysOfWeek']:
            day_counts[day] += 1
    
    # Calculate time gap score
    total_gap_score = 0
    num_gaps = 0
    
    # Sort sessions by day and time
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        day_sessions = [s for s in sessions if day in s['daysOfWeek']]
        day_sessions.sort(key=lambda x: convert_time_to_minutes(x['beginTime']))
        
        for i in range(len(day_sessions) - 1):
            gap = calculate_time_gap(day_sessions[i], day_sessions[i + 1])
            if gap < 60:  # Strongly prefer gaps less than 1 hour
                total_gap_score += (60 - gap) * 4  # Quadruple the score for sub-1-hour gaps
            elif gap < 120:  # Still prefer gaps less than 2 hours
                total_gap_score += (120 - gap) * 2
            elif gap < 180:  # Slightly prefer gaps less than 3 hours
                total_gap_score += (180 - gap)
            num_gaps += 1
    
    gap_score = total_gap_score / (num_gaps if num_gaps > 0 else 1)
    
    # Calculate day distribution score with much stronger day preferences
    day_weights = {
        'Monday': 1.5,     # Increased weight for Monday
        'Tuesday': 1.3,    # Increased weight for Tuesday
        'Wednesday': 1.1,  # Increased weight for Wednesday
        'Thursday': 0.5,   # Reduced weight for Thursday
        'Friday': 0.2      # Significantly reduced weight for Friday
    }
    
    # Add bonus for empty days (especially Thursday and Friday)
    empty_day_bonus = 0
    if 'Friday' not in day_counts:
        empty_day_bonus += 500
    if 'Thursday' not in day_counts:
        empty_day_bonus += 300
    
    # Add bonus for concentrated schedule
    used_days = len(day_counts)
    concentration_bonus = (5 - used_days) * 200  # Bonus points for using fewer days
    
    # Add extra bonus for very tight schedules (most gaps under 1 hour)
    tight_schedule_bonus = 0
    total_gaps = 0
    small_gaps = 0
    for day in day_counts:
        day_sessions = [s for s in sessions if day in s['daysOfWeek']]
        for i in range(len(day_sessions) - 1):
            gap = calculate_time_gap(day_sessions[i], day_sessions[i + 1])
            if gap < 60:
                small_gaps += 1
            total_gaps += 1
    
    if total_gaps > 0 and (small_gaps / total_gaps) > 0.5:
        tight_schedule_bonus = 300  # Bonus for having mostly small gaps
    
    day_score = sum(count * day_weights[day] for day, count in day_counts.items())
    
    return gap_score + day_score * 100 + empty_day_bonus + concentration_bonus + tight_schedule_bonus

def get_required_session_types(course_sessions):
    """Determine which session types are required for a course."""
    types = {'LEC': False, 'LAB': False, 'TUT': False}
    for session in course_sessions:
        types[session['meetingScheduleType']] = True
    return types

def select_best_schedule(course_data, time_preferences=None):
    """Select the best possible schedule without conflicts, respecting time preferences."""
    best_schedule = None
    best_score = float('-inf')
    
    def try_combinations(schedule, remaining_courses, selected_sessions):
        nonlocal best_schedule, best_score
        
        if not remaining_courses:
            score = calculate_schedule_score(selected_sessions)
            if score > best_score:
                best_score = score
                best_schedule = {k: v[:] for k, v in schedule.items()}
            return True
        
        course_code = remaining_courses[0]
        course_sessions = course_data[course_code]
        required_types = get_required_session_types(course_sessions)
        schedule[course_code] = []
        
        # Group sessions by type
        sessions_by_type = defaultdict(list)
        for session in course_sessions:
            # Skip sessions that don't meet time preferences
            if time_preferences and not time_preferences.is_time_allowed(session):
                continue
            sessions_by_type[session['meetingScheduleType']].append(session)
        
        # Sort sessions within each type by day preference and time
        for session_type in sessions_by_type:
            sessions_by_type[session_type].sort(
                key=lambda x: (
                    min(day_weights.get(day, 0) for day in x['daysOfWeek']),
                    convert_time_to_minutes(x['beginTime'])
                ),
                reverse=True
            )
        
        def try_session_type(schedule, course_code, remaining_types, selected_sessions):
            if not remaining_types:
                return try_combinations(schedule, remaining_courses[1:], selected_sessions)
            
            session_type = remaining_types[0]
            if not required_types[session_type]:
                return try_session_type(schedule, course_code, remaining_types[1:], selected_sessions)
            
            # If no valid sessions exist for a required type, return False
            if required_types[session_type] and not sessions_by_type[session_type]:
                return False
            
            for session in sessions_by_type[session_type]:
                if not any(check_time_conflict(session, existing) for existing in selected_sessions):
                    schedule[course_code].append(session)
                    selected_sessions.append(session)
                    
                    if try_session_type(schedule, course_code, remaining_types[1:], selected_sessions):
                        return True
                    
                    schedule[course_code].remove(session)
                    selected_sessions.remove(session)
            
            return False
        
        if not try_session_type(schedule, course_code, ['LEC', 'LAB', 'TUT'], selected_sessions):
            del schedule[course_code]
            return False
        
        return True
    
    # Define day weights for sorting
    global day_weights
    day_weights = {
        'Monday': 5,
        'Tuesday': 4,
        'Wednesday': 3,
        'Thursday': 2,
        'Friday': 1
    }
    
    # Start the recursive search
    try_combinations({}, list(course_data.keys()), [])
    
    return best_schedule if best_schedule else {}

def format_time(time_str):
    """Convert time from 24hr format to 12hr format."""
    time_obj = datetime.strptime(time_str, '%H%M')
    return time_obj.strftime('%I:%M %p').lstrip('0')

def organize_by_day(schedule):
    """Organize the schedule by day of the week."""
    days_schedule = defaultdict(list)
    
    day_order = {
        'Monday': 0,
        'Tuesday': 1,
        'Wednesday': 2,
        'Thursday': 3,
        'Friday': 4
    }
    
    for course_code, sessions in schedule.items():
        for session in sessions:
            for day in session['daysOfWeek']:
                # Format room based on building
                room = session.get('room', 'TBA')
                building = session.get('building', 'TBA')
                
                # If building is Shawenjigewining Hall, prefix room with "SHA"
                if building == "Shawenjigewining Hall" and room != 'TBA':
                    room = f"SHA{room}"
                
                session_info = {
                    'course_code': course_code,
                    'type': session['meetingScheduleType'],
                    'begin_time': session['beginTime'],
                    'end_time': session['endTime'],
                    'crn': session['courseReferenceNumber'],
                    'room': room,  # Use formatted room
                    'campus': session.get('campus', 'TBA'),
                    'building': building,
                    'prof': session.get('displayName', 'TBA')
                }
                days_schedule[day].append(session_info)
    
    sorted_schedule = {}
    for day in sorted(days_schedule.keys(), key=lambda x: day_order[x]):
        sorted_schedule[day] = sorted(days_schedule[day], 
                                    key=lambda x: convert_time_to_minutes(x['begin_time']))
    
    return sorted_schedule

def print_schedule_by_day(schedule):
    """Print the schedule organized by day."""
    daily_schedule = organize_by_day(schedule)
    
    print("\nWeekly Schedule:")
    print("=" * 70)
    
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        print(f"\n{day}:")
        print("-" * 70)
        
        if day not in daily_schedule or not daily_schedule[day]:
            print("  No classes scheduled")
            continue
            
        for session in daily_schedule[day]:
            print(f"  {session['course_code']} - {session['type']}")
            print(f"    {format_time(session['begin_time'])} - "
                  f"{format_time(session['end_time'])}")
            print(f"    Room: {session['room']}")
            print(f"    Campus: {session['campus']}")
            print(f"    CRN: {session['crn']}")
            print()

def schedule_to_json(schedule):
    """Convert schedule to a JSON-friendly format."""
    daily_schedule = organize_by_day(schedule)
    
    json_schedule = {
        'schedule_info': {
            'generated_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'total_courses': len(schedule)
        },
        'weekly_schedule': {}
    }
    
    # Convert daily schedule to JSON format
    for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']:
        if day in daily_schedule and daily_schedule[day]:
            json_schedule['weekly_schedule'][day] = [
                {
                    'course_code': session['course_code'],
                    'type': session['type'],
                    'start_time': format_time(session['begin_time']),
                    'end_time': format_time(session['end_time']),
                    'room': session['room'],
                    'campus': session['campus'],
                    'crn': session['crn'],
                    'building': session['building'],
                    'prof': session['prof']
                }
                for session in daily_schedule[day]
            ]
        else:
            json_schedule['weekly_schedule'][day] = []
    
    return json_schedule

# Modify the main() function in Algorithm.py
def main():
    """
    Main function to run the scheduling algorithm.
    Returns None and logs error if schedule cannot be generated.
    """
    try:
        print("Starting schedule generation...")
        ensure_directories()
        
        # Load course data
        try:
            combined_courses_path = os.path.join("Schedule Jsons", "combined_courses.json")
            with open(combined_courses_path, 'r') as f:
                course_data = json.load(f)
            print("Successfully loaded course data")
        except FileNotFoundError:
            log_error("combined_courses.json not found", traceback.format_exc())
            return None
        except json.JSONDecodeError:
            log_error("Error parsing combined_courses.json", traceback.format_exc())
            return None

        # Load time restrictions if provided
        try:
            restrictions_path = os.path.join("Schedule Jsons", "time_restrictions.json")
            with open(restrictions_path, 'r') as f:
                restrictions_data = json.load(f)
                
                # Helper function to get time range for a day
                def get_time_range(day_data):
                    start = day_data['start']
                    end = day_data['end']
                    if start == "0000" and end == "0000":
                        return {'earliest': '0000', 'latest': '2359'}
                    return {'earliest': start, 'latest': end}
                
                time_prefs = TimePreference({
                    'Monday': get_time_range(restrictions_data['monday']),
                    'Tuesday': get_time_range(restrictions_data['tuesday']),
                    'Wednesday': get_time_range(restrictions_data['wednesday']),
                    'Thursday': get_time_range(restrictions_data['thursday']),
                    'Friday': get_time_range(restrictions_data['friday'])
                })
                print("Successfully loaded time restrictions")
        except (FileNotFoundError, json.JSONDecodeError):
            time_prefs = TimePreference()
            print("No time restrictions found, using default preferences")

        # Validate schedule possibility
        is_valid, error_list = validate_schedule_possibility(course_data, time_prefs)
        if not is_valid:
            log_validity_errors(error_list)  # Directly pass the list
            return None
        print("Schedule validation successful")

        # Generate schedule
        print("Generating optimal schedule...")
        schedule = select_best_schedule(course_data, time_prefs)
        if not schedule:
            log_error("Schedule generation failed", 
                     "Could not generate a valid schedule with the given constraints")
            return None
        print("Successfully generated schedule")

        # Convert schedule to JSON and save
        try:
            json_schedule = schedule_to_json(schedule)
            schedule_path = os.path.join("Schedule Jsons", "generated_schedule.json")
            with open(schedule_path, 'w') as f:
                json.dump(json_schedule, f, indent=2)
            print("Successfully saved generated schedule to JSON")
            
            return json_schedule
        except Exception as e:
            log_error("Error saving generated schedule", traceback.format_exc())
            return None

    except Exception as e:
        log_error("Unexpected error in schedule generation", traceback.format_exc())
        return None

if __name__ == "__main__":
    main()
