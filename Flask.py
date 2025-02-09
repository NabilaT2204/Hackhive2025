from flask import Flask, request, jsonify
from flask_cors import CORS  # For CORS
import subprocess
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins

# Route to handle POST request from the frontend
@app.route('/courses', methods=['POST'])
def handle_courses():
    try:
        # Extracting the JSON data from the request
        data = request.get_json()  # This will parse the JSON body of the request
        courses = data.get('courses', [])  # Extract the 'courses' key from the JSON data

        # Ensure the courses are in the format you want (just for demonstration)
        if not courses:
            return jsonify({"error": "No courses provided"}), 400

        # Send courses to Scrapper.py via subprocess
        result = run_scraper(courses)

        # Return a response back to the frontend
        return jsonify({"status": "success", "message": "Scraper executed successfully", "courses": courses}), 200

    except Exception as e:
        # Handle any errors
        return jsonify({"error": str(e)}), 500

def run_scraper(courses):
    # Assuming your Scrapper.py is in the same directory
    try:
        # Running the Scraper.py script and passing courses as arguments
        result = subprocess.run(['python', 'Scrapper.py'] + courses, capture_output=True, text=True)
        print(result.stdout)  # Output from Scrapper.py
        if result.stderr:
            print(f"Error: {result.stderr}")  # Error output
        return result
    except Exception as e:
        print(f"Error running scraper: {e}")
        return None

if __name__ == '__main__':
    app.run(debug=True)
