from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import requests

#Search for a professor on RateMyProfessors and get their URL
def search_professor(prof_name):    
    # Ontario Tech's URL search on RateMyProf
    search_url = f"https://www.ratemyprofessors.com/search/professors/4714?q={prof_name.replace(' ', '%20')}"

    # Set up Selenium WebDriver
    chrome_options = Options()
    # Run in headless mode (no GUI)
    chrome_options.add_argument("--headless") 
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    # Open the search URL
    driver.get(search_url)

    try:
        # Find the first professor link
        first_prof = driver.find_element(By.XPATH, "//a[contains(@href, '/professor/')]")
        prof_url = first_prof.get_attribute("href")
    except Exception as e:
        print("Professor not found.")
        driver.quit()
        return None

    driver.quit()
    return prof_url

#Scrape comments from a professor's RateMyProfessors profile
def get_professor_comments(prof_url):
    
    # Mimic a real web browser request to avoid getting blocked by the website
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Makes an HTTP request to fetch a professor's page and checks if the request was successful (200).
    response = requests.get(prof_url, headers=headers)
    if response.status_code != 200:
        print("Failed to fetch professor's page.")
        return []

    # Use bs4 to parse the html
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Extract comments
    comments = soup.find_all("div", class_="Comments__StyledComments-dzzyvm-0 gRjWel")
    comments_list = [comment.get_text(strip=True) for comment in comments]
    
    return comments_list

# Enter professor Name and get the URL to their RateMyProf
prof_name = "Dan Walters"
prof_url = search_professor(prof_name)

#Check if prof_url is found
if prof_url:
    print(f"Found profile: {prof_url}")

    #retrieve comments and place in array
    comments = get_professor_comments(prof_url)

    if comments:
        print("Professor's comments:")
        for comment in comments:
            print("-", comment)
    else:
        print("No comments found.")
else:
    print("Could not find professor.")
