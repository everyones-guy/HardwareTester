document.addEventListener("DOMContentLoaded", () => {
    const userSettingsContainer = document.getElementById("user-settings");
    const globalSettingsContainer = document.getElementById("global-settings");
    const userSettingsForm = document.getElementById("user-settings-form");
    const globalSettingsForm = document.getElementById("update-global-setting-form");
    const globalSettingsList = document.getElementById("global-settings-list");

    /**
     * Fetch and display user settings.
     */
    async function loadUserSettings() {
        try {
            const data = await apiCall("/settings/user", "GET");

            if (data.success) {
                userSettingsContainer.innerHTML = "";
                Object.entries(data.settings).forEach(([key, value]) => {
                    userSettingsContainer.innerHTML += `
                        <div class="mb-3">
                            <label for="${key}" class="form-label">${key}</label>
                            <input type="text" class="form-control" id="${key}" name="${key}" value="${value}">
                        </div>`;
                });
            } else {
                alert("Failed to load user settings.");
            }
        } catch (error) {
            console.error("Error fetching user settings:", error);
            alert("Error loading user settings.");
        }
    }

    /**
     * Fetch and display global settings.
     */
    async function loadGlobalSettings() {
        try {
            const data = await apiCall("/settings/global", "GET");

            if (data.success) {
                globalSettingsContainer.innerHTML = "";
                Object.entries(data.settings).forEach(([key, value]) => {
                    globalSettingsContainer.innerHTML += `
                        <div class="mb-3">
                            <label for="${key}" class="form-label">${key}</label>
                            <input type="text" class="form-control" id="${key}" name="${key}" value="${value}">
                        </div>`;
                });
            } else {
                alert("Failed to load global settings.");
            }
        } catch (error) {
            console.error("Error fetching global settings:", error);
            alert("Error loading global settings.");
        }
    }

    /**
     * Handle user settings update.
     */
    if (userSettingsForm) {
        userSettingsForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const formData = new FormData(userSettingsForm);
            const settings = Object.fromEntries(formData);

            try {
                const response = await apiCall("/settings/user", "POST", { settings });
                alert(response.message || "User settings updated successfully.");
            } catch (error) {
                console.error("Error updating user settings:", error);
                alert("Failed to update user settings.");
            }
        });
    }

    /**
     * Fetch and display the list of global settings.
     */
    async function loadGlobalSettingsList() {
        try {
            const data = await apiCall("/settings/global/list", "GET");

            globalSettingsList.innerHTML = "";
            if (data.success && data.settings.length > 0) {
                data.settings.forEach((setting) => {
                    globalSettingsList.innerHTML += `
                        <li class="list-group-item">
                            <strong>${setting.key}</strong>: ${JSON.stringify(setting.value)}
                            <small class="text-muted float-end">Updated at: ${setting.updated_at}</small>
                        </li>`;
                });
            } else {
                globalSettingsList.innerHTML = "<li class='list-group-item text-danger'>No global settings found.</li>";
            }
        } catch (error) {
            console.error("Error fetching global settings list:", error);
            alert("Failed to load global settings.");
        }
    }

    /**
     * Handle global settings update.
     */
    if (globalSettingsForm) {
        globalSettingsForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const key = document.getElementById("key").value;
            let value;

            try {
                value = JSON.parse(document.getElementById("value").value);
            } catch (error) {
                alert("Invalid JSON format. Please check your input.");
                return;
            }

            try {
                const response = await apiCall("/settings/global", "POST", { key, value });
                alert(response.message || "Global setting updated successfully.");
                loadGlobalSettingsList();
            } catch (error) {
                console.error("Error updating global settings:", error);
                alert("Failed to update global settings.");
            }
        });
    }

    // **Initialize settings page**
    loadUserSettings();
    loadGlobalSettings();
    loadGlobalSettingsList();
});
