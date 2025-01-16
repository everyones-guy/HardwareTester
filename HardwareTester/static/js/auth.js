// auth.js

document.addEventListener("DOMContentLoaded", () => {
    console.log("Auth.js loaded successfully");

    // Highlight active navigation links
    const navLinks = document.querySelectorAll(".navbar-nav .nav-link");
    const currentPath = window.location.pathname;

    navLinks.forEach(link => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });

    // Handle sidebar navigation highlighting
    const sidebarLinks = document.querySelectorAll("aside ul li a");
    sidebarLinks.forEach(link => {
        if (link.getAttribute("href") === currentPath) {
            link.classList.add("active");
        } else {
            link.classList.remove("active");
        }
    });

    // Logout confirmation (optional)
    const logoutLink = document.querySelector("a[href='/auth/logout']");
    if (logoutLink) {
        logoutLink.addEventListener("click", (e) => {
            e.preventDefault();
            const confirmed = confirm("Are you sure you want to logout?");
            if (confirmed) {
                window.location.href = logoutLink.getAttribute("href");
            }
        });
    }

    // Example AJAX utility for authenticated areas
    function fetchData(url, method = "GET", data = null) {
        const options = {
            method,
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("[name=csrf_token]").value
            }
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        return fetch(url, options)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error("Error fetching data:", error);
                alert("An error occurred. Please try again.");
            });
    }

    // Example: Fetch notifications for authenticated users
    const notificationsContainer = document.querySelector("#notifications-container");
    if (notificationsContainer) {
        fetchData("/notifications/api")
            .then(data => {
                if (data.success) {
                    data.notifications.forEach(notification => {
                        const listItem = document.createElement("li");
                        listItem.textContent = notification.message;
                        notificationsContainer.appendChild(listItem);
                    });
                } else {
                    console.error("Failed to load notifications:", data.error);
                }
            });
    }
});
