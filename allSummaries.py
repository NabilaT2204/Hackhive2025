import json
import os
from typing import Dict, List, Optional, Set
from RateMyProf import load_professors, get_professor_url, scrape_reviews
from Summarizer import start_ollama_server, get_summary
from difflib import get_close_matches

def ensure_schedule_jsons_dir():
    """Ensure the Schedule Jsons directory exists."""
    os.makedirs("Schedule Jsons", exist_ok=True)

def initialize_reviews_file():
    """Clear and initialize the reviews file with an empty structure."""
    reviews_file = os.path.join("Schedule Jsons", "Reviews.json")
    initial_data = {
        "professors": {}  # Will store professor reviews as: "prof_name": {"reviews": [...]}
    }
    with open(reviews_file, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, indent=4, ensure_ascii=False)
    return reviews_file

def save_professor_reviews(professor_name: str, reviews: List[str]):
    """Add or update reviews for a professor in the reviews file."""
    reviews_file = os.path.join("Schedule Jsons", "Reviews.json")
    
    try:
        with open(reviews_file, 'r', encoding='utf-8') as f:
            all_reviews = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        all_reviews = {"professors": {}}
    
    all_reviews["professors"][professor_name] = {
        "reviews": reviews
    }
    
    with open(reviews_file, 'w', encoding='utf-8') as f:
        json.dump(all_reviews, f, indent=4, ensure_ascii=False)

def get_professor_reviews(professor_name: str) -> Optional[List[str]]:
    """Retrieve reviews for a specific professor from the reviews file."""
    reviews_file = os.path.join("Schedule Jsons", "Reviews.json")
    
    try:
        with open(reviews_file, 'r', encoding='utf-8') as f:
            all_reviews = json.load(f)
            prof_data = all_reviews["professors"].get(professor_name)
            return prof_data["reviews"] if prof_data else None
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def normalize_name(name: str) -> str:
    titles = ['Dr.', 'Prof.', 'Professor']
    name = name.strip()
    for title in titles:
        name = name.replace(title, '').strip()
    
    if ',' in name:
        last_name, first_name = name.split(',', 1)
        name = f"{first_name.strip()} {last_name.strip()}"
    
    parts = name.split()
    return ' '.join(part for part in parts if part).lower()

def format_display_name(name: str) -> str:
    if ',' in name:
        last_name, first_name = name.split(',', 1)
        return f"{first_name.strip()} {last_name.strip()}"
    return name

def find_matching_professor(prof_name: str, professors_data: List[dict]) -> Optional[dict]:
    normalized_search = normalize_name(prof_name)
    prof_dict = {normalize_name(p['name']): p for p in professors_data}
    
    if normalized_search in prof_dict:
        return prof_dict[normalized_search]
    
    matches = get_close_matches(normalized_search, prof_dict.keys(), n=1, cutoff=0.7)
    if matches:
        matched_name = matches[0]
        print(f"Matched '{format_display_name(prof_name)}' to '{prof_dict[matched_name]['name']}'")
        return prof_dict[matched_name]
    
    return None

def extract_professors_and_courses(schedule_file: str) -> Dict[str, Set[str]]:
    file_path = os.path.join("Schedule Jsons", schedule_file)
    with open(file_path, 'r') as f:
        schedule_data = json.load(f)
    
    professor_courses = {}
    weekly_schedule = schedule_data['weekly_schedule']
    
    for day in weekly_schedule.values():
        for class_info in day:
            prof = class_info.get('prof')
            if prof and prof != 'N/A':
                display_name = format_display_name(prof)
                course_code = class_info.get('course_code')
                
                if display_name not in professor_courses:
                    professor_courses[display_name] = set()
                
                if course_code:
                    professor_courses[display_name].add(course_code)
    
    return professor_courses

def get_professor_summary(prof_name: str, courses: Set[str], professors_data: List[dict]) -> dict:
    display_name = format_display_name(prof_name)
    print(f"\nProcessing professor: {display_name}")
    
    matched_prof = find_matching_professor(prof_name, professors_data)
    if not matched_prof:
        print(f"No matching professor found for {display_name}")
        return {
            'matched_name': display_name,
            'schedule_name': display_name,
            'courses': list(courses),
            'url': "",
            'summary': "Professor was not found in RateMyProf database",
            'review_count': 0
        }
    
    url = matched_prof['url']
    
    print(f"Scraping reviews for {matched_prof['name']}...")
    reviews = scrape_reviews(url)
    if not reviews:
        print("No reviews found")
        return {
            'matched_name': matched_prof['name'],
            'schedule_name': display_name,
            'courses': list(courses),
            'url': url,
            'summary': "No reviews found",
            'review_count': 0
        }
    
    # Save reviews for this professor
    save_professor_reviews(matched_prof['name'], reviews)
    reviews_text = '\n'.join(reviews)
    
    print("Generating summary...")
    summary = get_summary(matched_prof['name'], reviews_text)
    
    return {
        'matched_name': matched_prof['name'],
        'schedule_name': display_name,
        'courses': list(courses),
        'url': url,
        'summary': summary,
        'review_count': len(reviews)
    }

def main():
    print("Initializing Ollama server...")
    ollama_process = start_ollama_server()
    
    try:
        ensure_schedule_jsons_dir()
        
        # Initialize empty reviews file at the start
        print("Initializing reviews file...")
        initialize_reviews_file()
        
        professors_file = os.path.join("professorURLs", "ProfessorURLs.json")
        schedule_file = "generated_schedule.json"
        
        professor_courses = extract_professors_and_courses(schedule_file)
        print(f"Found {len(professor_courses)} professors in schedule")
        
        try:
            professors_data = load_professors(professors_file)
        except FileNotFoundError:
            print(f"Error: {professors_file} not found")
            return
        
        summaries = {}
        for prof, courses in professor_courses.items():
            summaries[prof] = get_professor_summary(prof, courses, professors_data)
        
        output_file = os.path.join("Schedule Jsons", "professor_summaries.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummaries saved to {output_file}")
        print(f"Successfully processed {len(summaries)} professors")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if ollama_process:
            print("Shutting down Ollama server...")
            ollama_process.terminate()

if __name__ == "__main__":
    main()
