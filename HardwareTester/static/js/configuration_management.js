$(document).ready(function () {
    const saveForm = $("#save-configuration-form");
    const savedList = $("#saved-configurations-list");
    const previewCard = $("#configuration-preview-card");
    const previewContent = $("#configuration-preview");
    const applyButton = $("#apply-configuration");
    const discardButton = $("#discard-preview");
    const saveConfigButton = $("#save-configuration");

    // Fetch saved configurations
    function fetchConfigurations() {
        $.ajax({
            url: "/configurations/list",
            method: "GET",
            success: function (data) {
                savedList.empty();
                if (data.success) {
                    data.configurations.forEach(function (config) {
                        const listItem = `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>${config.name}</span>
                                <div>
                                    <button class="btn btn-sm btn-primary preview-config" data-id="${config.id}">Preview</button>
                                </div>
                            </li>`;
                        savedList.append(listItem);
                    });
                } else {
                    savedList.html(`<li class="list-group-item text-danger">${data.error}</li>`);
                }
            },
            error: function (xhr) {
                console.error("Error fetching configurations:", xhr);
            },
        });
    }

    // Save current configuration
    saveConfigButton.on("click", function () {
        $.ajax({
            url: "/save-configuration",
            method: "POST",
            success: function (data) {
                if (data.success) {
                    alert("Configuration saved successfully!");
                    loadConfigurations();
                } else {
                    alert("Error saving configuration: " + data.message);
                }
            },
            error: function (xhr) {
                console.error("Error saving configuration:", xhr);
            },
        });
    });

    // Load configurations into the list
    function loadConfigurations() {
        $.ajax({
            url: "/get-configurations",
            method: "GET",
            success: function (data) {
                savedList.empty();
                if (data.success) {
                    data.configurations.forEach(function (config) {
                        const listItem = `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <strong>${config.name}</strong>
                                <button class="btn btn-primary btn-sm load-config" data-id="${config.id}">Load</button>
                            </li>`;
                        savedList.append(listItem);
                    });
                } else {
                    savedList.html("<li class='list-group-item text-danger'>Error loading configurations.</li>");
                }
            },
            error: function (xhr) {
                console.error("Error fetching configurations:", xhr);
            },
        });
    }

    // Load a specific configuration
    $(document).on("click", ".load-config", function () {
        const configId = $(this).data("id");
        $.ajax({
            url: `/load-configuration/${configId}`,
            method: "GET",
            success: function (data) {
                if (data.success) {
                    alert("Configuration loaded successfully!");
                } else {
                    alert("Error loading configuration: " + data.message);
                }
            },
            error: function (xhr) {
                console.error("Error loading configuration:", xhr);
            },
        });
    });

    // Save configuration
    saveForm.on("submit", function (event) {
        event.preventDefault();
        const name = $("#configuration-name").val();

        $.ajax({
            url: "/configurations/save",
            method: "POST",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": $("meta[name='csrf-token']").attr("content"),
            },
            data: JSON.stringify({ name, layout: {} }),
            success: function (data) {
                if (data.success) {
                    alert(data.message);
                    saveForm[0].reset();
                    fetchConfigurations();
                } else {
                    alert(`Error: ${data.error}`);
                }
            },
            error: function (xhr) {
                console.error("Error saving configuration:", xhr);
            },
        });
    });

    // Preview configuration
    $(document).on("click", ".preview-config", function () {
        const configId = $(this).data("id");
        $.ajax({
            url: `/configurations/preview/${configId}`,
            method: "GET",
            success: function (data) {
                if (data.success) {
                    previewContent.html(data.preview);
                    previewCard.removeClass("d-none");
                } else {
                    alert(`Error: ${data.error}`);
                }
            },
            error: function (xhr) {
                console.error("Error fetching preview:", xhr);
            },
        });
    });

    // Discard preview
    discardButton.on("click", function () {
        previewCard.addClass("d-none");
        previewContent.empty();
    });

    // Apply configuration (mock)
    applyButton.on("click", function () {
        alert("Configuration applied successfully.");
        discardButton.click();
    });

    // Initialize
    fetchConfigurations();
});
