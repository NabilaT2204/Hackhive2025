import json
import requests
from bs4 import BeautifulSoup

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

def save_reviews(reviews, filename="Reviews.txt"):
    """Save reviews to a text file."""
    with open(filename, 'w', encoding='utf-8') as f:
        for review in reviews:
            f.write(review + "\n")

def main():
    file_path = "ProfessorURLs.json"  # Path to the JSON file
    professors = load_professors(file_path)
    
    name = input("Enter professor's name: ")
    url = get_professor_url(professors, name)
    
    if not url:
        print("Professor not found.")
        return
    
    print(f"Scraping reviews for {name}...")
    reviews = scrape_reviews(url)
    
    if reviews:
        save_reviews(reviews)
        print("Reviews saved to Reviews.txt")
    else:
        print("No reviews found.")

if __name__ == "__main__":
    main()
