from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json
import os

app = Flask(__name__)
CORS(app)

# Constants for file paths
TIME_RESTRICTIONS_FILE = 'time_restrictions.json'
GENERATED_STRUCTURES_FILE = 'generated_structures.json'

@app.route('/courses', methods=['POST'])
def handle_courses():
    try:
        data = request.get_json()
        courses = data.get('courses', [])
        
        print("Starting scraper...")
        scraper_result = run_scraper(courses)
        print(f"Scraper result: {scraper_result}")
        
        if not scraper_result.get('success'):
            print("Scraper failed")
            return jsonify({"error": "Scraper failed", "details": scraper_result.get('error')}), 500

        print("Getting time restrictions...")
        time_restrictions = get_saved_time_restrictions()
        print(f"Time restrictions: {time_restrictions}")
        
        if not time_restrictions:
            print("No time restrictions found")
            algorithm_result = run_algorithm()
            return jsonify({"error": "No time restrictions found. Please set time restrictions first."}), 400

        print("Starting algorithm...")
        algorithm_result = run_algorithm()
        print(f"Algorithm result: {algorithm_result}")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/restrictions', methods=['POST'])
def handle_time_restrictions():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        time_restrictions = process_time_restrictions(data)
        
        # Validate time restrictions
        if not validate_time_restrictions(time_restrictions):
            return jsonify({"error": "Invalid time restrictions format"}), 400

        # Save time restrictions
        save_time_restrictions(time_restrictions)

        return jsonify({
            "status": "success",
            "message": "Time restrictions saved successfully",
            "time_restrictions": time_restrictions
        }), 200

    except Exception as e:
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
    """Save time restrictions to a JSON file"""
    try:
        with open(TIME_RESTRICTIONS_FILE, 'w') as f:
            json.dump(restrictions, f, indent=2)
    except IOError as e:
        raise Exception(f"Failed to save time restrictions: {str(e)}")

def get_saved_time_restrictions():
    """Retrieve saved time restrictions"""
    try:
        if not os.path.exists(TIME_RESTRICTIONS_FILE):
            return None
        with open(TIME_RESTRICTIONS_FILE, 'r') as f:
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
        # Run algorithm
        result = subprocess.run(['python', 'Algorithm.py'],
                              capture_output=True,
                              text=True,
                              check=True)
        
        # Parse the algorithm output
        try:
            algorithm_output = json.loads(result.stdout)
            
            # Save the generated structures
            with open(GENERATED_STRUCTURES_FILE, 'w') as f:
                json.dump(algorithm_output, f, indent=2)
            
            return {"success": True, "data": algorithm_output}
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON output from algorithm: {str(e)}"}
            
    except subprocess.CalledProcessError as e:
        return {"success": False, "error": f"Algorithm execution failed: {e.stderr}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == '__main__':
    app.run(debug=True)
