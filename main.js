document.addEventListener("DOMContentLoaded", function () {
    const courseContainer = document.getElementById("course-container");
    const addCourseButton = document.getElementById("add-course");
    const submitButton = document.getElementById("submit");

    addCourseButton.addEventListener("click", function () {
        const courseItems = document.querySelectorAll(".course-item");

        if (courseItems.length < 5) {
            const courseItem = document.createElement("div");
            courseItem.className = "course-item";

            const newInput = document.createElement("input");
            newInput.type = "text";
            newInput.className = "course-input";
            newInput.placeholder = "Enter course (e.g., CSCI4040)";

            // Add delete button only for additional courses
            if (courseItems.length > 0) {
                const deleteButton = document.createElement("button");
                deleteButton.className = "delete-course";
                deleteButton.textContent = "Delete";

                deleteButton.addEventListener("click", function () {
                    courseItem.remove();
                });

                courseItem.appendChild(deleteButton);
            }

            courseItem.insertBefore(newInput, courseItem.firstChild);
            courseContainer.appendChild(courseItem);
        } else {
            alert("You can only add up to 5 courses.");
        }
    });

    submitButton.addEventListener("click", function () {
        const courseInputs = document.querySelectorAll(".course-input");
        const courses = [];

        courseInputs.forEach(input => {
            if (input.value.trim() !== "") {
                courses.push(input.value.trim());
            }
        });
        console.log(courses);

        // Send courses to Python server using Fetch API
        fetch("http://127.0.0.1:5000/courses", {
            method: "POST",  // HTTP request method is POST, which is used for sending data to the server.
            headers: {
                "Content-Type": "application/json" // Set the Content-Type to application/json for sending JSON data
            },
            body: JSON.stringify({ courses: courses }) //This converts the 'courses' array into a JSON string and sends it in the body
        })
        //Catch errors
        .then(response => response.json())
        .then(data => {
            console.log("Server response:", data);
        })
        .catch(error => {
            console.error("Error sending data:", error);
        });
    });
});


// Get started button will scroll to the next section
document.addEventListener("DOMContentLoaded", function () {
    const getStartedButton = document.getElementById("Scroller");
    const aboutSection = document.getElementById("about");

    if (getStartedButton && aboutSection) {
        getStartedButton.addEventListener("click", function (event) {
            event.preventDefault(); // Prevent default anchor behavior
            aboutSection.scrollIntoView({ behavior: "smooth" });
        });
    }
});

document.addEventListener("DOMContentLoaded", () => {
    fetch("schedule_output.json") // Load the JSON file
        .then(response => response.json())
        .then(data => populateTable(data))
        .catch(error => console.error("Error loading JSON data:", error));
});

function populateTable(jsonData) {
    if (!jsonData.success) {
        console.error("Failed to generate schedule");
        return;
    }

    let table = document.querySelector("#courseSchedule table"); // Select the table inside #courseSchedule
    let tbody = table.getElementsByTagName("tbody")[0] || table; // Finds tbody if present

    // Clear existing rows except for the header
    while (tbody.rows.length > 1) {
        tbody.deleteRow(1);
    }

    jsonData.schedule.days.forEach(day => {
        day.classes.forEach(course => {
            let row = tbody.insertRow();
            row.insertCell().textContent = course.courseCode;
            row.insertCell().textContent = course.crn;
            row.insertCell().textContent = "N/A";
            row.insertCell().textContent = course.meetingType; 
            row.insertCell().textContent = day.dayName
            row.insertCell().textContent = formatTime(course.startTime) + " - " + formatTime(course.endTime);
        });
    });
}

// Function to convert military time (HH:MM) to standard 12-hour format
function formatTime(time) {
    let [hours, minutes] = time.split(":").map(Number);
    let period = hours >= 12 ? "PM" : "AM";
    hours = hours % 12 || 12;
    return `${hours}:${minutes.toString().padStart(2, "0")} ${period}`;
}
