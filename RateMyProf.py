import json
import requests
from bs4 import BeautifulSoup
import os

def ensure_schedule_jsons_dir():
    """Ensure the Schedule Jsons directory exists."""
    os.makedirs("Schedule Jsons", exist_ok=True)

def load_professors(file_path):
    """Load professors and their URLs from a JSON file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_professor_url(professors, name):
    """Retrieve the URL of the professor by name."""
    for prof in professors:
        if prof["name"].lower() == name.lower():
            return prof["url"]
    return None

def scrape_reviews(url):
    """Scrape reviews from the given RateMyProfessors URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print("Failed to retrieve page.")
        return []
    
    soup = BeautifulSoup(response.text, 'html.parser')
    reviews = []
    review_elements = soup.find_all("div", class_="Comments__StyledComments-dzzyvm-0" )
    
    for review in review_elements:
        reviews.append(review.get_text(strip=True))
    
    return reviews

def save_reviews(reviews, professor_name):
    """Save reviews to a JSON file in the Schedule Jsons folder."""
    ensure_schedule_jsons_dir()
    
    # Prepare the data structure
    review_data = {
        "professor": professor_name,
        "reviews": reviews
    }
    
    # Save to JSON file in the Schedule Jsons folder
    file_path = os.path.join("Schedule Jsons", "Reviews.json")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(review_data, f, indent=4, ensure_ascii=False)

def main():
    ensure_schedule_jsons_dir()
    
    # Update path to read from Schedule Jsons folder
    file_path = os.path.join("Schedule Jsons", "ProfessorURLs.json")
    
    try:
        professors = load_professors(file_path)
    except FileNotFoundError:
        print(f"Error: {file_path} not found")
        return
    except json.JSONDecodeError:
        print(f"Error: {file_path} is not a valid JSON file")
        return
    
    name = input("Enter professor's name: ")
    url = get_professor_url(professors, name)
    
    if not url:
        print("Professor not found.")
        return
    
    print(f"Scraping reviews for {name}...")
    reviews = scrape_reviews(url)
    
    if reviews:
        save_reviews(reviews, name)
        print("Reviews saved to Schedule Jsons/Reviews.json")
    else:
        print("No reviews found.")

if __name__ == "__main__":
    main()
