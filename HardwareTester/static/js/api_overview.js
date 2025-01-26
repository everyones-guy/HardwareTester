$(document).ready(function () {
    const responsePreview = $("#response-preview");
    const endpointDropdown = $("#endpoint");
    const availableEndpointsList = $("#available-endpoints");

    // Utility: Update Response Preview
    function updateResponsePreview(message, isError = false) {
        responsePreview.text(message);
        responsePreview.css("color", isError ? "red" : "black");
    }

    // Fetch and Populate Available Endpoints
    function loadAvailableEndpoints() {
        apiCall(
            "/api/endpoints",
            "GET",
            {},
            (data) => {
                availableEndpointsList.empty();
                endpointDropdown.empty();

                if (data.success && data.endpoints.length > 0) {
                    data.endpoints.forEach((endpoint) => {
                        availableEndpointsList.append(`<li class="list-group-item">${endpoint}</li>`);
                        endpointDropdown.append(`<option value="${endpoint}">${endpoint}</option>`);
                    });
                } else {
                    availableEndpointsList.html("<li class='list-group-item text-center'>No endpoints available.</li>");
                }
            },
            (xhr) => {
                const errorMessage = xhr.responseJSON?.error || "Failed to load endpoints.";
                console.error(errorMessage);
                updateResponsePreview(`Error: ${errorMessage}`, true);
            }
        );
    }

    // Handle API Test Form Submission
    function apiTestFormSubmission(event) {
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

        // API call using centralized function
        apiCall(
            endpoint,
            method,
            params,
            (response) => {
                updateResponsePreview(JSON.stringify(response, null, 2));
            },
            (xhr) => {
                const errorMessage = xhr.responseJSON?.error || "An error occurred while processing the request.";
                console.error(errorMessage);
                updateResponsePreview(`Error: ${errorMessage}`, true);
            }
        );
    }

    // Event listeners
    $("#api-test-form").on("submit", apiTestFormSubmission);
    $("#refresh-endpoints").on("click", function () {
        endpointDropdown.empty(); // Clear dropdown before reloading
        loadAvailableEndpoints();
    });

    // Initial load of available endpoints
    loadAvailableEndpoints();
});
