import json
from datetime import datetime, timedelta
from collections import defaultdict

class TimePreference:
    def __init__(self):
        self.restrictions = {
            'Monday': {'earliest': '0000', 'latest': '2359'},
            'Tuesday': {'earliest': '0000', 'latest': '2359'},
            'Wednesday': {'earliest': '0000', 'latest': '2359'},
            'Thursday': {'earliest': '0000', 'latest': '2359'},
            'Friday': {'earliest': '0000', 'latest': '2359'}
        }
    
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
    Returns (is_valid, error_message)
    """
    error_messages = []
    
    for course_code, sessions in course_data.items():
        # Get required session types for this course
        required_types = get_required_session_types(sessions)
        available_types = defaultdict(bool)
        
        # Check each session type
        for session in sessions:
            session_type = session['meetingScheduleType']
            if required_types[session_type]:
                if not time_preferences or time_preferences.is_time_allowed(session):
                    available_types[session_type] = True
        
        # Verify all required types are available
        missing_types = []
        for session_type, required in required_types.items():
            if required and not available_types[session_type]:
                missing_types.append(session_type)
        
        if missing_types:
            error_messages.append(
                f"Course {course_code} has no available {', '.join(missing_types)} "
                "sections within the specified time preferences"
            )
    
    is_valid = len(error_messages) == 0
    error_message = "\n".join(error_messages) if error_messages else ""
    return is_valid, error_message

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
                session_info = {
                    'course_code': course_code,
                    'type': session['meetingScheduleType'],
                    'begin_time': session['beginTime'],
                    'end_time': session['endTime'],
                    'crn': session['courseReferenceNumber'],
                    'room': session.get('room', 'TBA'),  # Add room
                    'campus': session.get('campus', 'TBA')  # Add campus
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
                    'crn': session['crn']
                }
                for session in daily_schedule[day]
            ]
        else:
            json_schedule['weekly_schedule'][day] = []
    
    return json_schedule

def main(json_data):
    # Parse the JSON data
    course_data = json.loads(json_data)
    
    # Create time preferences (optional)
    time_prefs = TimePreference()
    
    # Ask user if they want to set time preferences
    if input("Do you want to set time preferences? (yes/no): ").lower().strip() == 'yes':
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for day in days:
            if input(f"Set restrictions for {day}? (yes/no): ").lower().strip() == 'yes':
                earliest = input(f"Earliest time for {day} (24hr format, e.g., 1100) or press Enter to skip: ").strip()
                latest = input(f"Latest time for {day} (24hr format, e.g., 1700) or press Enter to skip: ").strip()
                
                if earliest or latest:
                    time_prefs.set_restriction(day, 
                                            earliest if earliest else None,
                                            latest if latest else None)
        
        # Validate schedule possibility before attempting to create schedule
        is_valid, error_message = validate_schedule_possibility(course_data, time_prefs)
        if not is_valid:
            print("\nERROR: Cannot create a valid schedule with these time preferences:")
            print(error_message)
            print("\nPlease try again with different time preferences.")
            return None
        
        schedule = select_best_schedule(course_data, time_prefs)
        
        # Double check that we got a complete schedule
        if not schedule or not all(bool(sessions) for sessions in schedule.values()):
            print("\nERROR: Could not create a complete schedule with these time preferences.")
            print("Some courses could not be scheduled while meeting all constraints.")
            print("Please try again with different time preferences.")
            return None
    else:
        schedule = select_best_schedule(course_data)
    
    # Print and export the schedule if it's valid
    if schedule:
        # Print the schedule
        print_schedule_by_day(schedule)
        
        # Convert schedule to JSON format
        json_schedule = schedule_to_json(schedule)
        
        # Save to file
        output_filename = 'generated_schedule.json'
        with open(output_filename, 'w') as f:
            json.dump(json_schedule, f, indent=2)
        
        print(f"\nSchedule has been exported to {output_filename}")
        return schedule
    else:
        print("\nERROR: Could not generate a valid schedule. Please try different preferences.")
        return None

if __name__ == "__main__":
    with open('combined_courses.json', 'r') as file:
        json_data = file.read()
    main(json_data)
