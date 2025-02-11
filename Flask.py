from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import subprocess
import json
import os
import traceback
import datetime
import shutil
from CalendarConverterICS import create_ics_from_json

app = Flask(__name__)
CORS(app)

# Folder where JSON and ICS files are stored
SCHEDULE_FOLDER = 'Schedule Jsons'
VALIDATION_FOLDER = 'validation'

# Ensure the folder exists
if not os.path.exists(SCHEDULE_FOLDER):
    os.makedirs(SCHEDULE_FOLDER)
if not os.path.exists(VALIDATION_FOLDER):
    os.makedirs(VALIDATION_FOLDER)

# Constants for file paths
TIME_RESTRICTIONS_FILE = 'time_restrictions.json'
GENERATED_STRUCTURES_FILE = 'generated_structures.json'

@app.route('/get-validation', methods=['GET'])
def get_validation():
    """Check if validity.json exists and return its contents."""
    validation_file = os.path.join(VALIDATION_FOLDER, "validity.json")

    if os.path.exists(validation_file):
        with open(validation_file, 'r') as f:
            validation_data = json.load(f)
        return jsonify(validation_data)
    else:
        return jsonify({"message": "No validation errors found"}), 404

@app.route('/clear-directories', methods=['POST'])
def clear_directories():
    try:
        # Clear Schedule Jsons directory
        if os.path.exists(SCHEDULE_FOLDER):
            for filename in os.listdir(SCHEDULE_FOLDER):
                file_path = os.path.join(SCHEDULE_FOLDER, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

        # Clear validation directory
        if os.path.exists(VALIDATION_FOLDER):
            for filename in os.listdir(VALIDATION_FOLDER):
                file_path = os.path.join(VALIDATION_FOLDER, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")

        return jsonify({"message": "Directories cleared successfully"}), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        log_error(error_trace)
        return jsonify({"error": str(e)}), 500

def log_error(error_message):
    """Log errors to a timestamped file in logs/Flask Logs/"""
    try:
        logs_dir = os.path.join('logs', 'Flask Logs')
        os.makedirs(logs_dir, exist_ok=True)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        log_filename = f"Flask_logs_{current_time}.txt"
        log_path = os.path.join(logs_dir, log_filename)
        with open(log_path, 'w') as log_file:
            log_file.write(error_message)
    except Exception as e:
        print(f"Failed to log error: {str(e)}")

@app.route('/list-schedules', methods=['GET'])
def list_schedules():
    try:
        files = [f for f in os.listdir(SCHEDULE_FOLDER) if f.endswith('.json') or f.endswith('.ics')]
        return jsonify({"files": files})
    except Exception as e:
        error_trace = traceback.format_exc()
        log_error(error_trace)
        return jsonify({"error": str(e)}), 500

@app.route('/get-schedule/<filename>', methods=['GET'])
def get_schedule(filename):
    try:
        file_path = os.path.join(SCHEDULE_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        error_trace = traceback.format_exc()
        log_error(error_trace)
        return jsonify({"error": str(e)}), 500

@app.route('/convert-calendar', methods=['GET'])
def convert_calendar():
    try:
        # Ensure the folder exists
        if not os.path.exists(SCHEDULE_FOLDER):
            os.makedirs(SCHEDULE_FOLDER)

        generated_schedule_path = os.path.join(SCHEDULE_FOLDER, 'generated_schedule.json')
        if not os.path.exists(generated_schedule_path):
            return jsonify({"error": "Schedule data not found"}), 404

        with open(generated_schedule_path, 'r') as f:
            schedule_data = json.load(f)

        calendar = create_ics_from_json(schedule_data)
        output_filename = os.path.join(SCHEDULE_FOLDER, 'schedule.ics')

        with open(output_filename, 'wb') as f:
            f.write(calendar.to_ical())

        if not os.path.exists(output_filename):
            return jsonify({"error": "Failed to create calendar file"}), 500

        return jsonify({"message": "Calendar file created successfully", "path": output_filename}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/courses', methods=['POST'])
def handle_courses():
    try:
        data = request.get_json()
        courses = data.get('courses', [])
        
        print("Starting scraper...")
        scraper_result = run_scraper(courses)
        if not scraper_result.get('success'):
            error_msg = f"Scraper failed: {scraper_result.get('error')}"
            log_error(error_msg)
            return jsonify({"error": error_msg}), 500

        print("Getting time restrictions...")
        time_restrictions = get_saved_time_restrictions()
        
        print("Starting algorithm...")
        algorithm_result = run_algorithm()
        
        if not algorithm_result.get('success'):
            error_message = algorithm_result.get('error', '')
            if "Cannot create valid schedule" in error_message:
                log_error(error_message)
                return jsonify({"error": error_message}), 400
            else:
                log_error(f"Algorithm failed: {error_message}")
                return jsonify({"error": f"Algorithm failed: {error_message}"}), 500

        print("Starting professor summaries generation...")
        summaries_result = run_summaries()
        if not summaries_result.get('success'):
            error_msg = f"Summaries failed: {summaries_result.get('error')}"
            log_error(error_msg)
            return jsonify({"error": error_msg}), 500

        return jsonify({"success": True, "message": "Schedule generated successfully"}), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        log_error(error_trace)
        return jsonify({"error": str(e)}), 500

@app.route('/restrictions', methods=['POST'])
def handle_time_restrictions():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        time_restrictions = process_time_restrictions(data)
        
        if not validate_time_restrictions(time_restrictions):
            return jsonify({"error": "Invalid time restrictions format"}), 400

        save_time_restrictions(time_restrictions)

        return jsonify({
            "status": "success",
            "message": "Time restrictions saved successfully",
            "time_restrictions": time_restrictions
        }), 200
    except Exception as e:
        error_trace = traceback.format_exc()
        log_error(error_trace)
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

def process_time_restrictions(data):
    """Process and validate time restrictions data"""
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
    time_restrictions = {}
    
    for day in days:
        start = data.get(f'{day}Start', '0000')
        end = data.get(f'{day}End', '2359')
        
        # Ensure proper time format (24-hour, 4 digits)
        start = start.zfill(4)
        end = end.zfill(4)
        
        time_restrictions[day] = {"start": start, "end": end}
    
    return time_restrictions

def validate_time_restrictions(restrictions):
    """Validate time restrictions format and values"""
    try:
        for day, times in restrictions.items():
            start = times['start']
            end = times['end']
            
            # Check format and range
            if not (len(start) == 4 and len(end) == 4):
                return False
            
            start_hour = int(start[:2])
            start_min = int(start[2:])
            end_hour = int(end[:2])
            end_min = int(end[2:])
            
            if not (0 <= start_hour <= 23 and 0 <= start_min <= 59 and
                   0 <= end_hour <= 23 and 0 <= end_min <= 59):
                return False
        
        return True
    except (ValueError, KeyError):
        return False

def save_time_restrictions(restrictions):
    """Save time restrictions to a JSON file in the Schedule Jsons folder"""
    try:
        # Ensure the Schedule Jsons folder exists
        if not os.path.exists(SCHEDULE_FOLDER):
            os.makedirs(SCHEDULE_FOLDER)
        
        # Define the full path for the time restrictions file
        file_path = os.path.join(SCHEDULE_FOLDER, TIME_RESTRICTIONS_FILE)
        
        # Save the restrictions to the file
        with open(file_path, 'w') as f:
            json.dump(restrictions, f, indent=2)
    except IOError as e:
        raise Exception(f"Failed to save time restrictions: {str(e)}")

def get_saved_time_restrictions():
    """Retrieve saved time restrictions from the Schedule Jsons folder"""
    try:
        # Define the full path for the time restrictions file
        file_path = os.path.join(SCHEDULE_FOLDER, TIME_RESTRICTIONS_FILE)
        
        # Check if the file exists
        if not os.path.exists(file_path):
            return None
        
        # Load and return the restrictions from the file
        with open(file_path, 'r') as f:
            return json.load(f)
    except (IOError, json.JSONDecodeError) as e:
        print(f"Error reading time restrictions: {str(e)}")
        return None

def run_scraper(courses):
    """Run the Scrapper.py script"""
    try:
        # Convert courses list to command-line arguments
        cmd = ['python', 'Scrapper.py'] + courses
        
        result = subprocess.run(cmd, 
                              capture_output=True,
                              text=True,
                              check=True)
        
        return {"success": True, "data": result.stdout}
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": e.stderr}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_algorithm():
    """Run the Algorithm.py script"""
    try:
        result = subprocess.run(['python', 'Algorithm.py'],
                              capture_output=True,
                              text=True)
        
        # Check if the process failed
        if result.returncode != 0:
            # Check for specific error messages in stderr
            error_output = result.stderr.strip()
            if error_output.startswith("ERROR: Cannot create valid schedule"):
                return {"success": False, "error": error_output}
            return {"success": False, "error": f"Algorithm execution failed: {error_output}"}
        
        # Correct path for generated_schedule.json
        generated_schedule_path = os.path.join(SCHEDULE_FOLDER, 'generated_schedule.json')
        if not os.path.exists(generated_schedule_path):
            return {"success": False, "error": "Failed to generate schedule"}
            
        return {"success": True}
            
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"Algorithm execution failed: {e.stderr}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def run_summaries():
    """Run the allSummaries.py script"""
    try:
        result = subprocess.run(['python', 'allSummaries.py'],
                               capture_output=True,
                               text=True,
                               check=True)
        
        # Correct path for professor_summaries.json
        summaries_path = os.path.join(SCHEDULE_FOLDER, 'professor_summaries.json')
        
        try:
            with open(summaries_path, 'r') as f:
                summaries_data = json.load(f)
            return {"success": True, "data": summaries_data}
        except (IOError, json.JSONDecodeError) as e:
            return {"success": False, "error": f"Failed to load professor summaries: {str(e)}"}
            
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"Summaries generation failed: {e.stderr}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    app.run(debug=True)
