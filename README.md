# Class Scheduler

## Overview

Class Scheduler is a powerful tool designed to help students organize their semester schedules efficiently. By allowing users to input their desired classes, the tool creates an optimized schedule that prioritizes organization and tries to provide days off whenever possible. It also integrates features to enhance the student experience, such as professor reviews and calendar downloads.

## Features

### 1. Optimized Schedule Generation
- Users can input the classes they want to take.
- The tool organizes their schedule to minimize gaps and maximize free days, ensuring an efficient semester plan.

### 2. Professor Reviews
- View summarized professor reviews from RateMyProf using the Deepseek-R1 model from Ollama.
- Gain insights into the quality of instruction and class expectations to make informed decisions.

### 3. Class Calendar
- Generate a downloadable calendar for your schedule.
- Easily visualize your class timings and plan your semester effectively.
- Calendar generation is powered by Deepseek-R1 from Ollama for seamless integration.

## Installation

### Prerequisites
- Python 3.8 or later
- Deepseek-R1 model from Ollama
- Required Python packages (specified below)

### Steps

1. Clone the repository:
   ```sh
   git clone https://github.com/your-username/class-scheduler.git
   cd class-scheduler
   ```

2. Install the required dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   *Or install individually:*
   ```sh
   pip install bs4 flask selenium webdriver icalendar pytz ollama requests flask_cors icalendar
   ```

3. Ensure you have access to the Deepseek-R1 model and configure it as per the documentation:
   ```sh
   ollama run deepseek-r1:1.5b
   ```

4. Run the application:
   ```sh
   python main.py
   ```

## Usage

- Start the program and input the classes you wish to take for the upcoming semester.
- The system will generate the most organized schedule, attempting to provide free days when possible.
- View detailed professor reviews for your selected classes to make informed decisions.
- Download your finalized class calendar for easy reference.

## Technologies Used

- **Python**: Core programming language.
- **Deepseek-R1**: AI-powered model for summarization and calendar generation.
- **RateMyProf**: Source of professor reviews.
- **ICS (iCalendar)**: For generating downloadable schedules.
- **BeautifulSoup (bs4)**: For web scraping tasks.
- **Flask**: To create a web interface for the tool.
- **Selenium & WebDriver**: For automated browsing tasks.
- **iCalendar & pytz**: For calendar creation and time zone management.

## Group Members

- Allan Sangle
- Nabila Tabassum
- Joseph Salama

## Acknowledgments

- Deepseek-R1 by Ollama for its powerful summarization and calendar capabilities.
- RateMyProfessors for providing valuable insights into professor reviews.
