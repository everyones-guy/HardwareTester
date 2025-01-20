$(document).ready(function () {
    const responsePreview = $("#response-preview");
    const endpointDropdown = $("#endpoint");
    const availableEndpointsList = $("#available-endpoints");
    const csrfToken = $('meta[name="csrf-token"]').content

    // Utility: Update Response Preview
    function updateResponsePreview(message, isError = false) {
        responsePreview.text(message);
        responsePreview.css("color", isError ? "red" : "black");
    }

    // Fetch and Populate Available Endpoints
    function loadAvailableEndpoints() {
        $.ajax({
            url: "/api/endpoints",
            method: "GET",
            success: function (data) {
                availableEndpointsList.empty();
                endpointDropdown.empty();

                if (data.success && data.endpoints.length > 0) {
                    data.endpoints.forEach(function (endpoint) {
                        availableEndpointsList.append(`<li class="list-group-item">${endpoint}</li>`);
                        endpointDropdown.append(`<option value="${endpoint}">${endpoint}</option>`);
                    });
                } else {
                    availableEndpointsList.html("<li class='list-group-item text-center'>No endpoints available.</li>");
                }
            },
            error: function (xhr) {
                const errorMessage = xhr.responseJSON?.error || "Failed to load endpoints.";
                console.error(errorMessage);
                updateResponsePreview(`Error: ${errorMessage}`, true);
            },
        });
    }

    // Handle API Test Form Submission
    $("#api-test-form").on("submit", function (event) {
        event.preventDefault();

        // Get input values
        const endpoint = endpointDropdown.val();
        const paramsInput = $("#params").val();
        let params = {};

        try {
            if (paramsInput.trim()) {
                params = JSON.parse(paramsInput);
            }
        } catch (error) {
            updateResponsePreview("Invalid JSON in parameters. Please check your input.", true);
            return;
        }

        // Determine request method
        const method = endpoint.includes("fetch") || endpoint.includes("list") ? "GET" : "POST";

        // Prepare AJAX options
        const ajaxOptions = {
            url: endpoint,
            method: method,
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": $("[name=csrf_token]").val()
            },
            success: function (data) {
                updateResponsePreview(JSON.stringify(data, null, 4));
            },
            error: function (xhr) {
                const errorMessage = xhr.responseJSON?.error || `Failed to send request to ${endpoint}.`;
                updateResponsePreview(`Error: ${errorMessage}`, true);
            },
        };

        // Add parameters for POST or query string for GET
        if (method === "POST") {
            ajaxOptions.data = JSON.stringify(params);
        } else if (method === "GET" && Object.keys(params).length > 0) {
            ajaxOptions.url += `?${$.param(params)}`;
        }

        // Send AJAX request
        $.ajax(ajaxOptions);
    });

    // Refresh Available Endpoints on Button Click
    $("#refresh-endpoints").on("click", function () {
        endpointDropdown.empty(); // Clear dropdown before reloading
        loadAvailableEndpoints();
    });

    // Initial load of available endpoints
    loadAvailableEndpoints();
});
