document.addEventListener("DOMContentLoaded", () => {
    // Initialize dashboard data
    if (document.getElementById("dashboard")) {
        fetchDashboardData();
    }

    // Handle contact form submission
    const contactForm = document.getElementById("contact-form");
    if (contactForm) {
        contactForm.addEventListener("submit", (event) => {
            event.preventDefault();
            submitContactForm(contactForm);
        });
    }

    // Live dashboard update simulation (Optional)
    if (document.getElementById("dashboard-live")) {
        setInterval(fetchDashboardData, 10000); // Refresh every 10 seconds
    }
});

// Fetch dashboard data
function fetchDashboardData() {
    fetch("/dashboard/data", {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
        },
    })
        .then((response) => {
            if (!response.ok) throw new Error("Failed to fetch dashboard data.");
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                updateDashboard(data.dashboard);
            } else {
                console.error("Error fetching dashboard data:", data.error);
            }
        })
        .catch((error) => console.error("Dashboard fetch error:", error));
}

// Update dashboard UI with new data
function updateDashboard(dashboard) {
    const statsContainer = document.getElementById("dashboard-stats");
    const logsContainer = document.getElementById("dashboard-logs");

    if (statsContainer) {
        statsContainer.innerHTML = `
            <h4>System Stats</h4>
            <ul>
                <li>Active Users: ${dashboard.active_users}</li>
                <li>Running Tests: ${dashboard.running_tests}</li>
                <li>Available Peripherals: ${dashboard.available_peripherals}</li>
            </ul>
        `;
    }

    if (logsContainer) {
        logsContainer.innerHTML = `
            <h4>Recent Logs</h4>
            <ul>
                ${dashboard.logs.map((log) => `<li>${log}</li>`).join("")}
            </ul>
        `;
    }
}

// Handle contact form submission
function submitContactForm(form) {
    const formData = new FormData(form);

    fetch("/contact", {
        method: "POST",
        body: JSON.stringify({
            name: formData.get("name"),
            email: formData.get("email"),
            message: formData.get("message"),
        }),
        headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": getCsrfToken(),
        },
    })
        .then((response) => {
            if (!response.ok) throw new Error("Failed to submit contact form.");
            return response.json();
        })
        .then((data) => {
            if (data.success) {
                alert(data.message || "Thank you for contacting us!");
                form.reset();
            } else {
                alert(data.error || "Failed to submit your message. Please try again.");
            }
        })
        .catch((error) => console.error("Contact form submission error:", error));
}

// Get CSRF token
function getCsrfToken() {
    return document.querySelector("meta[name='csrf-token']").getAttribute("content");
}
