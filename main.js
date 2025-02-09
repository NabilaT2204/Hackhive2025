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
        event.preventDefault(); // Prevents the page from scrolling to the top
        // Collect courses data
        const courseInputs = document.querySelectorAll(".course-input");
        const courses = [];
        courseInputs.forEach(input => {
            if (input.value.trim() !== "") {
                courses.push(input.value.trim());
            }
        });

        // Function to handle empty input and set default values if necessary
        function getTimeOrDefault(startId, endId) {
            const start = document.getElementById(startId).value;
            const end = document.getElementById(endId).value;
            return {
                start: start.trim() === "" ? "0000" : start,
                end: end.trim() === "" ? "2359" : end
            };
        }

        // Collect time restrictions data, setting default values if empty
        const timeRestrictions = {
            mondayStart: getTimeOrDefault('mondayStart', 'mondayEnd').start,
            mondayEnd: getTimeOrDefault('mondayStart', 'mondayEnd').end,
            tuesdayStart: getTimeOrDefault('tuesdayStart', 'tuesdayEnd').start,
            tuesdayEnd: getTimeOrDefault('tuesdayStart', 'tuesdayEnd').end,
            wednesdayStart: getTimeOrDefault('wednesdayStart', 'wednesdayEnd').start,
            wednesdayEnd: getTimeOrDefault('wednesdayStart', 'wednesdayEnd').end,
            thursdayStart: getTimeOrDefault('thursdayStart', 'thursdayEnd').start,
            thursdayEnd: getTimeOrDefault('thursdayStart', 'thursdayEnd').end,
            fridayStart: getTimeOrDefault('fridayStart', 'fridayEnd').start,
            fridayEnd: getTimeOrDefault('fridayStart', 'fridayEnd').end,
        };

        // Send both courses and time restrictions to the backend
        const data = {
            courses: courses,
            time_restrictions: timeRestrictions
        };

        // Send data to Python server using Fetch API
        fetch("http://127.0.0.1:5000/courses", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data) // Send both courses and time restrictions
        })
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
    fetch("generated_schedule.json") // Load the JSON file
        .then(response => response.json())
        .then(data => populateTable(data))
        .catch(error => console.error("Error loading JSON data:", error));
});

function populateTable(jsonData) {
    let table = document.querySelector("#courseSchedule table"); // Select the table inside #courseSchedule
    let tbody = table.getElementsByTagName("tbody")[0] || table; // Finds tbody if present

    // Clear existing rows except for the header
    while (tbody.rows.length > 1) {
        tbody.deleteRow(1);
    }

    // Loop through the weekly schedule
    for (let day in jsonData.weekly_schedule) {
        let dayName = day;
        jsonData.weekly_schedule[day].forEach(course => {
            let row = tbody.insertRow();
            row.insertCell().textContent = course.course_code;
            row.insertCell().textContent = course.crn;
            row.insertCell().textContent = course.room;
            row.insertCell().textContent = course.type; 
            row.insertCell().textContent = dayName;
            row.insertCell().textContent = `${course.start_time} - ${course.end_time}`;
            row.insertCell().textContent = course.campus
        });
    }
}
