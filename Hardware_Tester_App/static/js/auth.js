$(document).ready(function () {
    console.log("Auth.js loaded successfully");

    // Highlight active navigation links
    function highlightActiveLinks() {
        const currentPath = window.location.pathname;

        // Highlight navbar links
        $(".navbar-nav .nav-link").each(function () {
            $(this).toggleClass("active", $(this).attr("href") === currentPath);
        });

        // Highlight sidebar links
        $("aside ul li a").each(function () {
            $(this).toggleClass("active", $(this).attr("href") === currentPath);
        });
    }

    // Logout confirmation
    function setupLogoutConfirmation() {
        $("a[href='/auth/logout']").on("click", function (e) {
            e.preventDefault();
            if (confirm("Are you sure you want to logout?")) {
                window.location.href = $(this).attr("href");
            }
        });
    }

    // Fetch and display notifications
    async function fetchNotifications() {
        const notificationsContainer = $("#notifications-container");

        if (!notificationsContainer.length) return;

        try {
            const data = await apiCall("/notifications/api", "GET");

            notificationsContainer.empty();
            if (data.success && data.notifications.length > 0) {
                data.notifications.forEach((notification) => {
                    notificationsContainer.append(`<li>${notification.message}</li>`);
                });
            } else {
                notificationsContainer.html("<li>No new notifications.</li>");
            }
        } catch (error) {
            console.error("Failed to load notifications:", error);
            notificationsContainer.html("<li>Error loading notifications. Please try again later.</li>");
        }
    }

    // Initialize
    highlightActiveLinks();
    setupLogoutConfirmation();
    fetchNotifications();
});
