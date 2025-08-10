$(document).ready(function () {
    /**
     * Initialize dashboard data on page load
     */
    if ($("#dashboard").length) {
        fetchDashboardData();
    }

    /**
     * Handle contact form submission
     */
    const contactForm = $("#contact-form");
    if (contactForm.length) {
        contactForm.on("submit", function (event) {
            event.preventDefault();
            submitContactForm(contactForm);
        });
    }

    /**
     * Auto-refresh dashboard every 10 seconds (optional)
     */
    if ($("#dashboard-live").length) {
        setInterval(fetchDashboardData, 10000);
    }

    /**
     * Fetch Dashboard Data
     */
    async function fetchDashboardData() {
        try {
            const data = await apiCall("/api/dashboard/data", "GET");

            if (data.success) {
                updateDashboard(data.dashboard);
            } else {
                console.error("Dashboard Data Error:", data.error);
            }
        } catch (error) {
            console.error("Error fetching dashboard data:", error);
        }
    }

    /**
     * Update dashboard UI with new data
     */
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

    /**
     * Handle contact form submission
     */
    async function submitContactForm(form) {
        const formData = form.serializeArray();
        const payload = {};

        formData.forEach((item) => {
            payload[item.name] = item.value;
        });

        try {
            const data = await apiCall("/contact", "POST", payload);

            if (data.success) {
                alert(data.message || "Thank you for contacting us!");
                form[0].reset();
            } else {
                alert(data.error || "Failed to submit your message. Please try again.");
            }
        } catch (error) {
            console.error("Contact form submission error:", error);
            alert("An unexpected error occurred. Please try again later.");
        }
    }
});
