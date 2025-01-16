$(document).ready(function () {
    // Initialize dashboard data
    if ($("#dashboard").length) {
        fetchDashboardData();
    }

    // Handle contact form submission
    const contactForm = $("#contact-form");
    if (contactForm.length) {
        contactForm.on("submit", function (event) {
            event.preventDefault();
            submitContactForm(contactForm);
        });
    }

    // Live dashboard update simulation (Optional)
    if ($("#dashboard-live").length) {
        setInterval(fetchDashboardData, 10000); // Refresh every 10 seconds
    }

    // Fetch dashboard data
    function fetchDashboardData() {
        $.ajax({
            url: "/dashboard/data",
            method: "GET",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCsrfToken(),
            },
            success: function (data) {
                if (data.success) {
                    updateDashboard(data.dashboard);
                } else {
                    console.error("Error fetching dashboard data:", data.error);
                }
            },
            error: function (xhr) {
                console.error("Dashboard fetch error:", xhr);
            },
        });
    }

    // Update dashboard UI with new data
    function updateDashboard(dashboard) {
        const statsContainer = $("#dashboard-stats");
        const logsContainer = $("#dashboard-logs");

        if (statsContainer.length) {
            statsContainer.html(`
                <h4>System Stats</h4>
                <ul>
                    <li>Active Users: ${dashboard.active_users}</li>
                    <li>Running Tests: ${dashboard.running_tests}</li>
                    <li>Available Peripherals: ${dashboard.available_peripherals}</li>
                </ul>
            `);
        }

        if (logsContainer.length) {
            logsContainer.html(`
                <h4>Recent Logs</h4>
                <ul>
                    ${dashboard.logs.map((log) => `<li>${log}</li>`).join("")}
                </ul>
            `);
        }
    }

    // Handle contact form submission
    function submitContactForm(form) {
        const formData = form.serializeArray();
        const payload = {};
        formData.forEach((item) => {
            payload[item.name] = item.value;
        });

        $.ajax({
            url: "/contact",
            method: "POST",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
            data: JSON.stringify(payload),
            success: function (data) {
                if (data.success) {
                    alert(data.message || "Thank you for contacting us!");
                    form[0].reset();
                } else {
                    alert(data.error || "Failed to submit your message. Please try again.");
                }
            },
            error: function (xhr) {
                console.error("Contact form submission error:", xhr);
            },
        });
    }

    // Get CSRF token
    function getCsrfToken() {
        return $("meta[name='csrf-token']").attr("content");
    }
});
