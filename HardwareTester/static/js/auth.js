$(document).ready(function () {
    console.log("Auth.js loaded successfully");

    // Highlight active navigation links
    function highlightActiveLinks() {
        const currentPath = window.location.pathname;

        // Highlight navbar links
        $(".navbar-nav .nav-link").each(function () {
            if ($(this).attr("href") === currentPath) {
                $(this).addClass("active");
            } else {
                $(this).removeClass("active");
            }
        });

        // Highlight sidebar links
        $("aside ul li a").each(function () {
            if ($(this).attr("href") === currentPath) {
                $(this).addClass("active");
            } else {
                $(this).removeClass("active");
            }
        });
    }

    // Logout confirmation
    function setupLogoutConfirmation() {
        const logoutLink = $("a[href='/auth/logout']");
        if (logoutLink.length) {
            logoutLink.on("click", function (e) {
                e.preventDefault();
                const confirmed = confirm("Are you sure you want to logout?");
                if (confirmed) {
                    window.location.href = $(this).attr("href");
                }
            });
        }
    }

    // Fetch and display notifications
    function fetchNotifications() {
        const notificationsContainer = $("#notifications-container");

        if (notificationsContainer.length) {
            apiCall("/notifications/api", "GET", null, (data) => {
                if (data.success) {
                    notificationsContainer.empty();

                    if (data.notifications.length > 0) {
                        data.notifications.forEach((notification) => {
                            const listItem = `<li>${notification.message}</li>`;
                            notificationsContainer.append(listItem);
                        });
                    } else {
                        notificationsContainer.html("<li>No new notifications.</li>");
                    }
                } else {
                    console.error("Failed to load notifications:", data.error);
                    notificationsContainer.html("<li>Failed to load notifications.</li>");
                }
            }, (xhr) => {
                console.error("Error fetching notifications:", xhr);
                notificationsContainer.html("<li>Error loading notifications. Please try again later.</li>");
            });
        }
    }

    // Initialize
    highlightActiveLinks();
    setupLogoutConfirmation();
    fetchNotifications();

});
