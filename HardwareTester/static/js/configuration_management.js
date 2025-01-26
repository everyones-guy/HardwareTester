$(document).ready(function () {
    const savedList = $("#saved-configurations-list");
    const previewCard = $("#configuration-preview-card");
    const previewContent = $("#configuration-preview");
    const applyButton = $("#apply-configuration");
    const discardButton = $("#discard-preview");
    const saveForm = $("#save-configuration-form");

    // Fetch and display saved configurations
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
                showAlert("Failed to fetch configurations. Please try again later.", "danger");
                console.error("Error fetching configurations:", xhr);
            }
        );
    }

    // Save a configuration
    saveForm.on("submit", function (event) {
        event.preventDefault();
        const name = $("#configuration-name").val();
        const layout = {}; // Placeholder for the configuration layout

        if (!name) {
            showAlert("Please provide a name for the configuration.", "warning");
            return;
        }

        apiCall(
            "/configurations/save",
            "POST",
            { name, layout },
            (data) => {
                showAlert(data.message || "Configuration saved successfully.", "success");
                saveForm[0].reset();
                fetchConfigurations();
            },
            (xhr) => {
                showAlert("Failed to save configuration. Please try again later.", "danger");
                console.error("Error saving configuration:", xhr);
            }
        );
    });

    // Preview a configuration
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
                    showAlert(`Error: ${data.error}`, "danger");
                }
            },
            (xhr) => {
                showAlert("Failed to load configuration preview.", "danger");
                console.error("Error fetching preview:", xhr);
            }
        );
    });

    // Apply a configuration
    $(document).on("click", ".apply-config", function () {
        const configId = $(this).data("id");

        apiCall(
            `/configurations/apply/${configId}`,
            "POST",
            null,
            (data) => {
                showAlert(data.message || "Configuration applied successfully.", "success");
            },
            (xhr) => {
                showAlert("Failed to apply configuration. Please try again later.", "danger");
                console.error("Error applying configuration:", xhr);
            }
        );
    });

    // Discard preview
    discardButton.on("click", function () {
        previewCard.addClass("d-none");
        previewContent.empty();
    });

    // Initial fetch
    fetchConfigurations();
});
