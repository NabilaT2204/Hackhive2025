from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import json

app = Flask(__name__)
CORS(app)

@app.route('/courses', methods=['POST'])
def handle_courses():
    try:
        data = request.get_json()
        courses = data.get('courses', [])

        if not courses:
            return jsonify({"error": "No courses provided"}), 400

        # Send courses to Scrapper.py
        scraper_result = run_scraper(courses)
        
        # After scraper runs successfully, run the algorithm
        algorithm_result = run_algorithm(courses, get_saved_time_restrictions())

        return jsonify({
            "status": "success", 
            "message": "Scraper and Algorithm executed successfully",
            "courses": courses,
            "algorithm_result": algorithm_result
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/restrictions', methods=['POST'])
def handle_time_restrictions():
    try:
        data = request.get_json()
        time_restrictions = process_time_restrictions(data)
        
        # Save time restrictions for later use
        save_time_restrictions(time_restrictions)

        return jsonify({
            "status": "success",
            "message": "Time restrictions saved successfully",
            "time_restrictions": time_restrictions
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_time_restrictions(data):
    """Process and validate time restrictions data"""
    time_restrictions = {
        "monday": {"start": data.get('mondayStart', '0000'), "end": data.get('mondayEnd', '2359')},
        "tuesday": {"start": data.get('tuesdayStart', '0000'), "end": data.get('tuesdayEnd', '2359')},
        "wednesday": {"start": data.get('wednesdayStart', '0000'), "end": data.get('wednesdayEnd', '2359')},
        "thursday": {"start": data.get('thursdayStart', '0000'), "end": data.get('thursdayEnd', '2359')},
        "friday": {"start": data.get('fridayStart', '0000'), "end": data.get('fridayEnd', '2359')}
    }
    return time_restrictions

def save_time_restrictions(restrictions):
    """Save time restrictions to a JSON file"""
    with open('time_restrictions.json', 'w') as f:
        json.dump(restrictions, f)

def get_saved_time_restrictions():
    """Retrieve saved time restrictions"""
    try:
        with open('time_restrictions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def run_scraper(courses):
    """Run the Scrapper.py script"""
    try:
        result = subprocess.run(['python', 'Scrapper.py'] + courses, 
                              capture_output=True, text=True, check=True)
        print("Scraper output:", result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Scraper error: {e.stderr}")
        raise Exception(f"Scraper failed: {e.stderr}")

def run_algorithm(courses, time_restrictions):
    """Run the Algorithm.py script with courses and time restrictions"""
    try:
        # Convert data to JSON string for passing to Algorithm.py
        input_data = json.dumps({
            "courses": courses,
            "time_restrictions": time_restrictions
        })
        
        # Run Algorithm.py with the input data
        result = subprocess.run(['python', 'Algorithm.py'],
                              input=input_data,
                              capture_output=True,
                              text=True,
                              check=True)
        
        # Parse the algorithm output (assuming it returns JSON)
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"raw_output": result.stdout}
            
    except subprocess.CalledProcessError as e:
        print(f"Algorithm error: {e.stderr}")
        raise Exception(f"Algorithm failed: {e.stderr}")

if __name__ == '__main__':
    app.run(debug=True)