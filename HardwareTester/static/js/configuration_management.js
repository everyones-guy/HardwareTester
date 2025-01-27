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
    function fetchConfigurations() {
        apiCall(
            "/configurations/list",
            "GET",
            null,
            (data) => {
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
            },
            (xhr) => {
                showAlert("Failed to fetch configurations. Please try again later.", true);
                console.error("Error fetching configurations:", xhr);
            }
        );
    }

    /**
     * Save a new configuration.
     */
    saveForm.on("submit", function (event) {
        event.preventDefault();
        const name = $("#configuration-name").val();
        const layout = {}; // Placeholder for the configuration layout

        if (!name) {
            showAlert("Please provide a name for the configuration.", true);
            return;
        }

        apiCall(
            "/api/configurations/save",
            "POST",
            { name, layout },
            (data) => {
                showAlert(data.message || "Configuration saved successfully.", false);
                saveForm[0].reset();
                fetchConfigurations();
            },
            (xhr) => {
                showAlert("Failed to save configuration. Please try again later.", true);
                console.error("Error saving configuration:", xhr);
            }
        );
    });

    /**
     * Preview a configuration.
     */
    $(document).on("click", ".preview-config", function () {
        const configId = $(this).data("id");

        apiCall(
            `/configurations/preview/${configId}`,
            "GET",
            null,
            (data) => {
                if (data.success) {
                    previewContent.html(data.preview);
                    previewCard.removeClass("d-none");
                } else {
                    showAlert(`Error: ${data.error}`, true);
                }
            },
            (xhr) => {
                showAlert("Failed to load configuration preview.", true);
                console.error("Error fetching preview:", xhr);
            }
        );
    });

    /**
     * Apply a configuration.
     */
    $(document).on("click", ".apply-config", function () {
        const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
        const configName = $(this).data("name");
        const decodedConfigName = decodeURIComponent(configName); // Decode the name

        apiCall(
            `/api/configurations/${encodeURIComponent(configName)}`,
            "GET",
            null,
            (data) => {
                if (data.success) {
                    showAlert(data.message || "Configuration fetched successfully.", false);
                    console.log("Fetched Configuration:", data.configuration);
                } else {
                    showAlert(data.error || "Configuration not found.", true);
                }
            },
            (xhr) => {
                showAlert("Failed to fetch configuration. Please try again.", true);
                console.error("Error fetching configuration:", xhr);
            }
        );
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
