// Initialize all functionality
document.addEventListener("DOMContentLoaded", async function () {
    // Check if this is the very first load of the main page
    const isFirstLoad = !sessionStorage.getItem('hasLoaded');
    
    if (isFirstLoad) {
        try {
            const response = await fetch("http://127.0.0.1:5000/clear-directories", {
                method: "POST",
            });

            if (!response.ok) {
                throw new Error(`Failed to clear directories: ${response.status}`);
            }

            console.log("Directories cleared successfully");
            // Set the flag indicating we've loaded once
            sessionStorage.setItem('hasLoaded', 'true');
        } catch (error) {
            console.error("Error clearing directories:", error);
        }
    }

    console.log("DOM loaded, initializing all components...");
    initializeDownloadButton();
    initializeCourseManagement();
    initializeScroll();
    initializeTables();
    fetchValidationErrors();
});

// Clear on refresh
window.addEventListener("beforeunload", async function (event) {
    try {
        const xhr = new XMLHttpRequest();
        xhr.open("POST", "http://127.0.0.1:5000/clear-directories", false);
        xhr.send();
    } catch (error) {
        console.error("Error clearing directories on refresh:", error);
    }
});

function initializeDownloadButton() {
    const courseSchedule = document.getElementById("course-schedule");
    if (!courseSchedule) {
        console.error("Course schedule container not found!");
        return;
    }

    const downloadCalendarButton = document.createElement("button");
    downloadCalendarButton.id = "download-calendar";
    downloadCalendarButton.textContent = "Download Calendar";
    downloadCalendarButton.className = "download-calendar-button"; // Updated class name
    
    courseSchedule.appendChild(downloadCalendarButton);

    downloadCalendarButton.addEventListener("click", async function() {
        try {
            const convertResponse = await fetch("http://127.0.0.1:5000/convert-calendar", {
                method: "GET",
            });

            if (!convertResponse.ok) {
                throw new Error(`HTTP error! Status: ${convertResponse.status}`);
            }

            const blob = await convertResponse.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = "schedule.ics";
            
            document.body.appendChild(a);
            a.click();
            
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
        } catch (error) {
            console.error("Error downloading calendar:", error);
            alert("Failed to download calendar. Please try again.");
        }
    });
}

async function fetchValidationErrors() {
    try {
        const response = await fetch("http://127.0.0.1:5000/get-validation");

        if (!response.ok) {
            if (response.status === 404) {
                console.log("No validation errors found.");
                return;
            }
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        displayValidationErrors(data);
    } catch (error) {
        console.error("Error fetching validation errors:", error);
    }
}

function displayValidationErrors(data) {
    const container = document.getElementById("validation-errors");

    if (!container) {
        console.error("Validation errors container not found.");
        return;
    }

    container.innerHTML = ""; // Clear previous content

    if (data.validation_errors && data.validation_errors.length > 0) {
        data.validation_errors.forEach(error => {
            const errorElement = document.createElement("div");
            errorElement.className = "error-message";
            errorElement.style.cssText = `
                color: red;
                background-color: #ffeeee;
                padding: 10px;
                border-radius: 5px;
                margin-bottom: 10px;
            `;
            errorElement.innerHTML = `<strong>${error.course}</strong>: ${error.message}`;
            container.appendChild(errorElement);
        });
    }
}

function initializeCourseManagement() {
    const courseContainer = document.getElementById("course-container");
    const addCourseButton = document.getElementById("add-course");
    const submitButton = document.getElementById("submit");

    if (!courseContainer || !addCourseButton || !submitButton) {
        console.error("Required elements not found for course management!");
        return;
    }

    addCourseButton.addEventListener("click", function() {
        console.log("Add course button clicked");
        const courseItems = document.querySelectorAll(".course-item");

        if (courseItems.length < 5) {
            const courseItem = document.createElement("div");
            courseItem.className = "course-item";

            const newInput = document.createElement("input");
            newInput.type = "text";
            newInput.className = "course-input";
            newInput.placeholder = "Enter course (e.g., CSCI4040)";

            const deleteButton = document.createElement("button");
            deleteButton.className = "delete-course-button"; // Updated class name
            deleteButton.textContent = "X";
            deleteButton.style.marginLeft = "10px";

            deleteButton.addEventListener("click", function() {
                courseItem.remove();
            });

            courseItem.appendChild(newInput);
            courseItem.appendChild(deleteButton);
            courseContainer.appendChild(courseItem);
        } else {
            alert("You can only add up to 5 courses.");
        }
    });

    submitButton.addEventListener("click", handleSubmit);
}

async function handleSubmit(event) {
    event.preventDefault();

    const errorDisplay = document.getElementById("schedule-error");
    if (errorDisplay) {
        errorDisplay.remove();
    }

    const courseInputs = document.querySelectorAll(".course-input");
    const courses = [];
    courseInputs.forEach(input => {
        if (input.value.trim() !== "") {
            courses.push(input.value.trim());
        }
    });

    const timeRestrictions = {
        mondayStart: formatTimeValue(document.getElementById('mondayStart').value),
        mondayEnd: formatTimeValue(document.getElementById('mondayEnd').value),
        tuesdayStart: formatTimeValue(document.getElementById('tuesdayStart').value),
        tuesdayEnd: formatTimeValue(document.getElementById('tuesdayEnd').value),
        wednesdayStart: formatTimeValue(document.getElementById('wednesdayStart').value),
        wednesdayEnd: formatTimeValue(document.getElementById('wednesdayEnd').value),
        thursdayStart: formatTimeValue(document.getElementById('thursdayStart').value),
        thursdayEnd: formatTimeValue(document.getElementById('thursdayEnd').value),
        fridayStart: formatTimeValue(document.getElementById('fridayStart').value),
        fridayEnd: formatTimeValue(document.getElementById('fridayEnd').value)
    };

    try {
        const restrictionsResponse = await fetch("http://127.0.0.1:5000/restrictions", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(timeRestrictions)
        });

        if (!restrictionsResponse.ok) {
            throw new Error("Failed to save time restrictions");
        }

        const coursesResponse = await fetch("http://127.0.0.1:5000/courses", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ courses: courses })
        });

        if (!coursesResponse.ok) {
            const errorData = await coursesResponse.json();
            throw new Error(errorData.error || "Failed to process courses");
        }

        const data = await coursesResponse.json();

        if (data.success) {
            setTimeout(() => {
                initializeTables();
            }, 1000);
        } else {
            throw new Error(data.error || "No schedule data received");
        }

    } catch (error) {
        console.error("Error:", error);
        displayError(error.message);
    }
}

function formatTimeValue(value) {
    if (!value) return "0000";
    value = value.replace(/\D/g, '');
    return value.padStart(4, '0');
}

function createErrorDisplay() {
    const errorDisplay = document.createElement("div");
    errorDisplay.id = "schedule-error";
    errorDisplay.className = "error-message";
    errorDisplay.style.cssText = `
        display: none;
        color: #dc2626;
        background-color: #fee2e2;
        border: 1px solid #dc2626;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 0.375rem;
        text-align: center;
    `;
    
    const scheduleTable = document.getElementById("course-schedule");
    if (scheduleTable) {
        scheduleTable.parentNode.insertBefore(errorDisplay, scheduleTable);
    }
    
    return errorDisplay;
}

function displayError(message) {
    let errorDisplay = document.getElementById("schedule-error");

    if (!errorDisplay) {
        errorDisplay = createErrorDisplay();
    }

    errorDisplay.textContent = message;
    errorDisplay.style.display = "block";
}

function initializeScroll() {
    const getStartedButton = document.getElementById("get-started");
    const aboutSection = document.getElementById("about");

    if (getStartedButton && aboutSection) {
        getStartedButton.addEventListener("click", function(event) {
            event.preventDefault();
            aboutSection.scrollIntoView({ behavior: "smooth" });
        });
    }
}

function initializeTables() {
    // Load schedule table
    fetch("http://127.0.0.1:5000/get-schedule/generated_schedule.json")
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load schedule (Status: ${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            if (Object.keys(data).length === 0) {
                throw new Error("No schedule data available");
            }
            populateTable(data);
        })
        .catch(error => {
            console.error("Error loading schedule:", error);
            displayError("Failed to load course schedule. Please try generating a schedule first.");
        });

    // Load professor summary table
    fetch("http://127.0.0.1:5000/get-schedule/professor_summaries.json")
        .then(response => {
            if (!response.ok) {
                throw new Error(`Failed to load professor summaries (Status: ${response.status})`);
            }
            return response.json();
        })
        .then(data => {
            if (Object.keys(data).length === 0) {
                throw new Error("No professor data available");
            }
            window.professorData = data;
            populateProfessorSummaryTable();
        })
        .catch(error => {
            console.error("Error loading professor data:", error);
            displayError("Failed to load professor summaries. Please try generating a schedule first.");
        });
}

function populateTable(jsonData) {
    const table = document.querySelector("#course-schedule table");
    if (!table) {
        console.error("Schedule table not found");
        return;
    }
    
    let tbody = table.querySelector("tbody");
    if (!tbody) {
        tbody = document.createElement("tbody");
        table.appendChild(tbody);
    }

    // Clear existing rows
    tbody.innerHTML = '';

    if (!jsonData.weekly_schedule) {
        displayError("Invalid schedule data format");
        return;
    }

    for (let day in jsonData.weekly_schedule) {
        jsonData.weekly_schedule[day].forEach(course => {
            const row = tbody.insertRow();
            row.insertCell().textContent = course.course_code || 'N/A';
            row.insertCell().textContent = course.crn || 'N/A';
            row.insertCell().textContent = course.room || 'N/A';
            row.insertCell().textContent = course.type || 'N/A';
            row.insertCell().textContent = day;
            row.insertCell().textContent = `${course.start_time || 'N/A'} - ${course.end_time || 'N/A'}`;
            row.insertCell().textContent = course.campus || 'N/A';
        });
    }
}

function populateProfessorSummaryTable() {
    const table = document.querySelector("#summary table");
    if (!table) {
        console.error("Summary table not found");
        return;
    }

    let tbody = table.querySelector("tbody");
    if (!tbody) {
        tbody = document.createElement("tbody");
        table.appendChild(tbody);
    }

    // Clear existing rows
    tbody.innerHTML = '';

    if (!window.professorData) {
        displayError("Professor data is not loaded");
        return;
    }

    Object.keys(window.professorData).forEach(professorName => {
        const professor = window.professorData[professorName];
        const row = tbody.insertRow();

        row.insertCell().textContent = professor.courses ? professor.courses.join(", ") : 'N/A';
        
        const nameCell = row.insertCell();
        if (professor.url && professor.url.trim() !== '') {
            nameCell.innerHTML = `<a href="${professor.url}" target="_blank">${professor.matched_name || professorName}</a>`;
        } else {
            nameCell.textContent = professor.matched_name || professorName;
        }
        
        row.insertCell().textContent = professor.summary || 'No summary available';
    });
}
