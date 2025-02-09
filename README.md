# Class Scheduler

A powerful tool to help students organize their semester schedules efficiently with AI-powered optimizations and professor insights.

## Overview

Class Scheduler helps students organize their semester schedules by optimizing class timings, maximizing free days, and providing professor reviews. It also enables calendar downloads for seamless integration with personal planners.

## Features

### 1. Optimized Schedule Generation  
- Input desired classes and get a gap-minimized schedule  
- Prioritizes free days for better work-life balance  

### 2. Professor Reviews  
- AI-summarized reviews from RateMyProf (powered by Deepseek-R1)  
- Insights into teaching quality and class expectations  

### 3. Class Calendar Integration  
- Download schedules as ICS files  
- Visualize timings with automatic timezone conversion  

## Installation

### Prerequisites
- Python 3.8+
- [Ollama](https://ollama.ai/) (for Deepseek-R1)
- Deepseek-R1 model:  
  ```bash
  ollama run deepseek-r1:1.5b
Setup
Clone repository:

bash
Copy
git clone https://github.com/your-username/class-scheduler.git
cd class-scheduler
Install dependencies:

bash
Copy
pip install -r requirements.txt
or individually:

bash
Copy
pip install bs4 flask selenium webdriver-manager icalendar pytz ollama requests
Run application:

bash
Copy
python main.py
Usage
Start the program

Input your desired classes

Review optimized schedule options

Check professor ratings

Download final calendar (ICS format)

Tech Stack
Backend: Python, Flask

AI Integration: Ollama (Deepseek-R1 1.5B)

Web Scraping: BeautifulSoup, Selenium

Scheduling: iCalendar, pytz

Frontend: HTML/CSS (Basic UI)

Development Team
Allan Sangle

Nabila Tabassum

Joseph Salama

Acknowledgments
Deepseek-R1 team at Ollama for AI capabilities

RateMyProfessors for review data
