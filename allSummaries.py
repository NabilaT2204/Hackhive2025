import json
import subprocess
import time
from typing import Dict, List, Optional, Set
from RateMyProf import load_professors, get_professor_url, scrape_reviews, save_reviews
from Summarizer import start_ollama_server, get_summary
from difflib import get_close_matches

def normalize_name(name: str) -> str:
    """Normalize a name by converting from 'Last, First' to 'First Last' format and removing titles."""
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
    """Convert name from 'Last, First' to 'First Last' format for display."""
    if ',' in name:
        last_name, first_name = name.split(',', 1)
        return f"{first_name.strip()} {last_name.strip()}"
    return name

def find_matching_professor(prof_name: str, professors_data: List[dict]) -> Optional[dict]:
    """Find a professor in the data using fuzzy matching."""
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
    """Extract unique professors and their corresponding courses from the schedule JSON file."""
    with open(schedule_file, 'r') as f:
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

def get_professor_summary(prof_name: str, courses: Set[str], professors_data: List[dict]) -> Optional[dict]:
    """Get reviews and generate summary for a single professor."""
    display_name = format_display_name(prof_name)
    print(f"\nProcessing professor: {display_name}")
    
    matched_prof = find_matching_professor(prof_name, professors_data)
    if not matched_prof:
        print(f"No matching professor found for {display_name}")
        return None
    
    url = matched_prof['url']
    
    print(f"Scraping reviews for {matched_prof['name']}...")
    reviews = scrape_reviews(url)
    if not reviews:
        print("No reviews found")
        return None
    
    save_reviews(reviews)
    
    print("Generating summary...")
    summary = get_summary('\n'.join(reviews))
    
    return {
        'matched_name': matched_prof['name'],
        'schedule_name': display_name,
        'courses': list(courses),  # Convert set to list for JSON serialization
        'url': url,
        'summary': summary,
        'review_count': len(reviews)
    }

def main():
    print("Initializing Ollama server...")
    ollama_process = start_ollama_server()
    
    try:
        # Load schedule and extract professors with their courses
        professor_courses = extract_professors_and_courses('generated_schedule.json')
        print(f"Found {len(professor_courses)} professors in schedule")
        
        try:
            professors_data = load_professors('ProfessorURLs.json')
        except FileNotFoundError:
            print("Error: ProfessorURLs.json not found")
            return
        
        # Process each professor and collect summaries
        summaries = {}
        for prof, courses in professor_courses.items():
            result = get_professor_summary(prof, courses, professors_data)
            if result:
                summaries[prof] = result
        
        output_file = 'professor_summaries.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summaries, f, indent=2, ensure_ascii=False)
        
        print(f"\nSummaries saved to {output_file}")
        print(f"Successfully processed {len(summaries)} out of {len(professor_courses)} professors")
        
        if len(summaries) < len(professor_courses):
            print("\nProfessors not found:")
            for prof in professor_courses:
                if prof not in summaries:
                    print(f"- {prof}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        if ollama_process:
            print("Shutting down Ollama server...")
            ollama_process.terminate()

if __name__ == "__main__":
    main()
