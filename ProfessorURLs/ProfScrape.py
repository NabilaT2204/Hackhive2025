import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException, StaleElementReferenceException

BASE_URL = "https://www.ratemyprofessors.com/search/professors/4714"  # Ontario Tech University

def setup_driver():
    """Sets up and returns a Selenium Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-popup-blocking")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def handle_overlays(driver):
    """Attempt to close any overlays that might be present."""
    try:
        cookie_buttons = driver.find_elements(By.CSS_SELECTOR, "[aria-label='Accept all cookies']")
        if cookie_buttons:
            driver.execute_script("arguments[0].click();", cookie_buttons[0])
            time.sleep(1)
        
        close_buttons = driver.find_elements(By.CSS_SELECTOR, "button[aria-label='Close']")
        for button in close_buttons:
            driver.execute_script("arguments[0].click();", button)
            time.sleep(1)
            
    except Exception as e:
        print(f"Note: Attempted to handle overlays - {str(e)}")

def load_all_professors(driver):
    """Click the 'Show More' button until all professors are loaded."""
    retry_count = 0
    max_retries = 3
    
    while True:
        try:
            handle_overlays(driver)
            
            wait = WebDriverWait(driver, 10)
            show_more_button = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "PaginationButton__StyledPaginationButton-txi1dr-1"))
            )
            
            driver.execute_script("arguments[0].scrollIntoView(true);", show_more_button)
            driver.execute_script("arguments[0].click();", show_more_button)
            print("🔄 Loading more professors...")
            
            retry_count = 0
            time.sleep(2)
            
        except NoSuchElementException:
            print("✅ All professors loaded!")
            break
            
        except (ElementClickInterceptedException, TimeoutException) as e:
            retry_count += 1
            if retry_count >= max_retries:
                print("⚠️ Maximum retries reached, continuing with available results...")
                break
                
            print(f"⚠️ Click failed (attempt {retry_count}/{max_retries}), trying again...")
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

def extract_professor_info(driver):
    """Extract information for all professors on the page."""
    professors_data = []
    wait = WebDriverWait(driver, 10)
    
    try:
        # Wait for the cards to be present
        cards = wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a[href*='/professor/']")
            )
        )
        
        total_professors = len(cards)
        print(f"📊 Found {total_professors} professors")
        
        for index, card in enumerate(cards, 1):
            try:
                # Extract URL directly from the anchor tag
                url = card.get_attribute('href')
                
                # Find name within the card
                name_element = card.find_element(By.CLASS_NAME, "CardName__StyledCardName-sc-1gyrgim-0")
                name = name_element.text.strip()
                
                print(f"[{index}/{total_professors}] {name} - {url}")
                professors_data.append({
                    'id': index,
                    'name': name,
                    'profile_url': url
                })
                
            except StaleElementReferenceException:
                print(f"⚠️ Stale element encountered at index {index}, refreshing elements...")
                time.sleep(1)
                cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/professor/']")
                continue
                
            except Exception as e:
                print(f"⚠️ Error processing professor #{index}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"❌ Error extracting professors: {str(e)}")
    
    return professors_data

def save_to_json(professors_data, filename="professors.json"):
    """Save professor data to a JSON file."""
    try:
        data = {
            'total_professors': len(professors_data),
            'last_updated': time.strftime('%Y-%m-%d %H:%M:%S'),
            'professors': professors_data
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"✅ Data saved to {filename}")
    except Exception as e:
        print(f"❌ Error saving JSON file: {str(e)}")

if __name__ == "__main__":
    driver = setup_driver()

    try:
        print("🌐 Accessing RateMyProfessors...")
        driver.get(BASE_URL)
        time.sleep(3)
        
        print("📚 Loading all professors...")
        load_all_professors(driver)
        
        print("🔍 Extracting professor information...")
        professors_data = extract_professor_info(driver)
        
        if professors_data:
            print(f"\n✅ Successfully processed {len(professors_data)} professors")
            save_to_json(professors_data)
        else:
            print("❌ No professor data was extracted")
            
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
    finally:
        driver.quit()
