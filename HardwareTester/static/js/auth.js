$(document).ready(function () {
    console.log("Auth.js loaded successfully");

    // Highlight active navigation links
    $(".navbar-nav .nav-link").each(function () {
        const currentPath = window.location.pathname;
        if ($(this).attr("href") === currentPath) {
            $(this).addClass("active");
        } else {
            $(this).removeClass("active");
        }
    });

    // Handle sidebar navigation highlighting
    $("aside ul li a").each(function () {
        const currentPath = window.location.pathname;
        if ($(this).attr("href") === currentPath) {
            $(this).addClass("active");
        } else {
            $(this).removeClass("active");
        }
    });

    // Logout confirmation (optional)
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

    // Example AJAX utility for authenticated areas
    function fetchData(url, method = "GET", data = null) {
        const options = {
            url: url,
            method: method,
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": $("[name=csrf_token]").val()
            },
            dataType: "json",
            success: function (response) {
                return response;
            },
            error: function (xhr, status, error) {
                console.error("Error fetching data:", error);
                alert("An error occurred. Please try again.");
            }
        };

        if (data) {
            options.data = JSON.stringify(data);
        }

        return $.ajax(options);
    }

    // Example: Fetch notifications for authenticated users
    const notificationsContainer = $("#notifications-container");
    if (notificationsContainer.length) {
        fetchData("/notifications/api")
            .done(function (data) {
                if (data.success) {
                    data.notifications.forEach(function (notification) {
                        const listItem = `<li>${notification.message}</li>`;
                        notificationsContainer.append(listItem);
                    });
                } else {
                    console.error("Failed to load notifications:", data.error);
                }
            });
    }
});
