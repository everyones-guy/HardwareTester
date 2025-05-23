$(document).ready(function () {
    const savedList = $("#saved-configurations-list");
    const previewCard = $("#configuration-preview-card");
    const previewContent = $("#configuration-preview");
    const applyButton = $("#apply-configuration");
    const discardButton = $("#discard-preview");
    const saveForm = $("#save-configuration-form");

    /**
     * Fetch and display saved configurations.
     */
    async function fetchConfigurations() {
        try {
            const data = await apiCall("/api/configurations/list", "GET");
            savedList.empty();

            if (data.success && data.configurations.length > 0) {
                data.configurations.forEach((config) => {
                    savedList.append(`
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            <strong>${config.name}</strong>
                            <div>
                                <button class="btn btn-primary btn-sm preview-config" data-id="${config.id}">Preview</button>
                                <button class="btn btn-success btn-sm apply-config ms-2" data-id="${config.id}">Apply</button>
                            </div>
                        </li>
                    `);
                });
            } else {
                savedList.html("<li class='list-group-item text-center'>No configurations available.</li>");
            }
        } catch (error) {
            showAlert("Failed to fetch configurations. Please try again later.", true);
            console.error("Error fetching configurations:", error);
        }
    }

    /**
     * Save a new configuration and commit it to the database.
     */
    saveForm.on("submit", async function (event) {
        event.preventDefault();
        const name = $("#configuration-name").val();
        const layout = {}; // Placeholder for the configuration layout

        if (!name) {
            showAlert("Please provide a name for the configuration.", true);
            return;
        }

        try {
            const data = await apiCall("/api/configurations/save", "POST", { name, layout });

            if (data.success) {
                showAlert(data.message || "Configuration saved successfully.");
                saveForm[0].reset();
                fetchConfigurations();
            } else {
                showAlert(data.error || "Failed to save configuration.", true);
            }
        } catch (error) {
            showAlert("Failed to save configuration. Please try again later.", true);
            console.error("Error saving configuration:", error);
        }
    });

    /**
     * Preview a configuration.
     */
    $(document).on("click", ".preview-config", async function () {
        const configId = $(this).data("id");

        try {
            const data = await apiCall(`/api/configurations/preview/${configId}`, "GET");

            if (data.success) {
                previewContent.html(data.preview);
                previewCard.removeClass("d-none");
            } else {
                showAlert(data.error || "Failed to load preview.", true);
            }
        } catch (error) {
            showAlert("Failed to load configuration preview.", true);
            console.error("Error fetching preview:", error);
        }
    });

    /**
     * Apply a configuration and commit it to the database.
     */
    $(document).on("click", ".apply-config", async function () {
        const configId = $(this).data("id");

        try {
            const data = await apiCall(`/api/configurations/apply/${configId}`, "POST");

            if (data.success) {
                showAlert(data.message || "Configuration applied successfully.");

                try {
                    const commitResponse = await apiCall("/api/configurations/commit", "POST", {
                        configuration: data.configuration,
                    });
                    showAlert(commitResponse.message || "Configuration committed successfully.");
                } catch (commitError) {
                    showAlert("Failed to commit configuration to the database.", true);
                    console.error("Error committing configuration:", commitError);
                }
            } else {
                showAlert(data.error || "Failed to apply configuration.", true);
            }
        } catch (error) {
            showAlert("Failed to apply configuration.", true);
            console.error("Error applying configuration:", error);
        }
    });

    /**
     * Discard configuration preview.
     */
    discardButton.on("click", function () {
        previewCard.addClass("d-none");
        previewContent.empty();
    });

    /**
     * Utility: Show alerts for user feedback.
     */
    function showAlert(message, isError = false) {
        alert(isError ? `Error: ${message}` : message);
    }

    // Initial fetch of configurations
    fetchConfigurations();
});
