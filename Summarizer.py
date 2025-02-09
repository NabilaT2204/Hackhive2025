import requests
import subprocess
import time
import atexit
import sys

def start_ollama_server():
    try:
        subprocess.run(["ollama", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("Error: Ollama not installed or not in PATH")
        sys.exit(1)

    try:
        requests.get("http://localhost:11434", timeout=2)
        print("Ollama server already running")
        return None
    except requests.ConnectionError:
        print("Starting Ollama server...")

    process = subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.PIPE
    )
    
    for _ in range(30):
        try:
            requests.get("http://localhost:11434", timeout=1)
            print("Ollama server started successfully")
            break
        except requests.ConnectionError:
            time.sleep(0.5)
    else:
        print("Failed to start Ollama server after 15 seconds")
        sys.exit(1)
    
    print("Checking model availability...")
    time.sleep(2)
    try:
        pull_response = requests.post("http://localhost:11434/api/pull", 
            json={"name": "deepseek-r1:1.5b"},
            timeout=30
        )
        if pull_response.status_code != 200:
            print(f"Error pulling model: {pull_response.text}")
            sys.exit(1)
        print("Model ready")
    except requests.RequestException as e:
        print(f"Error pulling model: {str(e)}")
        sys.exit(1)
    
    return process

def extract_final_response(text):
    # Split by </think> and get the last part
    parts = text.split("</think>")
    if len(parts) > 1:
        # Get everything after the last </think> tag
        final_part = parts[-1].strip()
        
        # Remove any remaining <think> tags that might be at the start
        if final_part.startswith("<think>"):
            final_part = final_part[final_part.find("</think>") + 8:].strip()
            
        # If there's a "Final response:" marker, split on that
        if "Final response:" in final_part:
            final_part = final_part.split("Final response:", 1)[1]
            
        return final_part.strip()
    return text.strip()

def get_summary(text):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "deepseek-r1:1.5b",
                "prompt": f"""
                The text provided is reviews of a professor. Each line is a different review made by a different person.
                Write a brief summary of this text (about 3-4 sentences).
                Heres an example of what it should look like: [professor name] is an outstanding professor who excels in his teaching, supports everyone's well-being, and is genuinely humorous, making every room a better place. He’s also a fantastic mentor for students seeking practical experience:
                Be honest with whether the reviews like the professor, or dislike, and create an opinion on it: {text}
                """,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 150,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1
                }
            },
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"Error generating summary: {response.text}")
            return None
            
        result = response.json()
        if "response" not in result:
            print(f"Unexpected API response: {result}")
            return None
            
        # Extract just the final response
        full_response = result["response"].strip()
        final_response = extract_final_response(full_response)
        
        if not final_response:
            print("Warning: Empty summary received")
            
        return final_response
        
    except requests.RequestException as e:
        print(f"Error calling Ollama API: {str(e)}")
        return None

def main():
    process = None
    try:
        process = start_ollama_server()
        
        try:
            with open("Reviews.txt", "r", encoding='utf-8') as f:
                reviews = f.read()
                print(f"Read {len(reviews)} characters from Reviews.txt")
        except FileNotFoundError:
            print("Error: Reviews.txt file not found")
            return
        except Exception as e:
            print(f"Error reading file: {str(e)}")
            return
            
        if not reviews.strip():
            print("Error: Reviews.txt is empty")
            return
            
        summary = get_summary(reviews)
        if summary:
            print("\nSummary:")
            print(summary)
        else:
            print("Failed to generate summary")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if process:
            process.terminate()

if __name__ == "__main__":
    main()
