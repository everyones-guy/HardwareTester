// Fetch and render user settings
function loadUserSettings() {
    $.getJSON("/settings/user", function (data) {
        if (data.success) {
            const settings = data.settings;
            let settingsHtml = "";
            for (const key in settings) {
                settingsHtml += `
                    <div class="mb-3">
                        <label for="${key}" class="form-label">${key}</label>
                        <input type="text" class="form-control" id="${key}" name="${key}" value="${settings[key]}">
                    </div>
                `;
            }
            $("#user-settings").html(settingsHtml);
        } else {
            alert("Failed to fetch user settings: " + data.error);
        }
    });
}

// Fetch and render global settings
function loadGlobalSettings() {
    $.getJSON("/settings/global", function (data) {
        if (data.success) {
            const settings = data.settings;
            let settingsHtml = "";
            for (const key in settings) {
                settingsHtml += `
                    <div class="mb-3">
                        <label for="${key}" class="form-label">${key}</label>
                        <input type="text" class="form-control" id="${key}" name="${key}" value="${settings[key]}">
                    </div>
                `;
            }
            $("#global-settings").html(settingsHtml);
        } else {
            alert("Failed to fetch global settings: " + data.error);
        }
    });
}

// Handle user settings form submission
$("#user-settings-form").on("submit", function (event) {
    event.preventDefault();
    const formData = {};
    $(this).serializeArray().forEach((item) => {
        formData[item.name] = item.value;
    });

    $.ajax({
        url: "/settings/user",
        method: "POST",
        contentType: "application/json",
        headers: {
            "X-CSRFToken": $("meta[name='csrf-token']").attr('content')  // Ensure CSRF token is sent
        },
        data: JSON.stringify({ settings: formData }),
        success: function (response) {
            alert("User settings updated successfully!");
        },
        error: function () {
            alert("Failed to update user settings.");
        },
    });
});

// Fetch and display global settings
function loadGlobalSettingsList() {
    $.get("/settings/global", function (data) {
        const list = $("#global-settings-list");
        list.empty();
        if (data.success) {
            data.settings.forEach((setting) => {
                list.append(`
                    <li class="list-group-item">
                        <strong>${setting.key}</strong>: ${JSON.stringify(setting.value)}
                        <small class="text-muted float-end">Updated at: ${setting.updated_at}</small>
                    </li>
                `);
            });
        } else {
            list.append(`<li class="list-group-item text-danger">${data.message}</li>`);
        }
    });
}

// Handle global setting updates
$("#update-global-setting-form").on("submit", function (event) {
    event.preventDefault();
    const key = $("#key").val();
    const value = JSON.parse($("#value").val());

    $.post("/settings/global", { key, value }, function (data) {
        if (data.success) {
            alert(data.message);
            loadGlobalSettingsList();
        } else {
            alert(data.message);
        }
    });
});

// Initialize settings page
$(document).ready(function () {
    loadUserSettings();
    loadGlobalSettings();
});
