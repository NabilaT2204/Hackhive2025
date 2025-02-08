document.addEventListener("DOMContentLoaded", function () {
    const courseContainer = document.getElementById("course-container");
    const addCourseButton = document.getElementById("add-course");

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
});

document.addEventListener("DOMContentLoaded", function () {
    const scrollButton = document.getElementById("Scroller");
    const aboutSection = document.getElementById("about");

    scrollButton.addEventListener("click", function () {
        aboutSection.scrollIntoView({ behavior: "smooth" });
    });
});
