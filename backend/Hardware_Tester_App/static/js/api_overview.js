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
    async function loadAvailableEndpoints() {
        try {
            availableEndpointsList.empty();
            endpointDropdown.empty();

            const data = await apiCall("/api/endpoints", "GET");

            if (data.success && data.endpoints.length > 0) {
                data.endpoints.forEach((endpoint) => {
                    availableEndpointsList.append(`<li class="list-group-item">${endpoint}</li>`);
                    endpointDropdown.append(`<option value="${endpoint}">${endpoint}</option>`);
                });
            } else {
                availableEndpointsList.html("<li class='list-group-item text-center'>No endpoints available.</li>");
            }
        } catch (error) {
            console.error("Failed to load endpoints:", error);
            updateResponsePreview(`Error: ${error.error || "Failed to load endpoints."}`, true);
        }
    }

    // Handle API Test Form Submission
    async function apiTestFormSubmission(event) {
        event.preventDefault();

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

        const method = endpoint.includes("fetch") || endpoint.includes("list") ? "GET" : "POST";

        try {
            const response = await apiCall(endpoint, method, params);
            updateResponsePreview(JSON.stringify(response, null, 2));
        } catch (error) {
            console.error("API request failed:", error);
            updateResponsePreview(`Error: ${error.error || "An error occurred while processing the request."}`, true);
        }
    }

    // Event listeners
    $("#api-test-form").on("submit", apiTestFormSubmission);
    $("#refresh-endpoints").on("click", function () {
        endpointDropdown.empty();
        loadAvailableEndpoints();
    });

    // Initial load of available endpoints
    loadAvailableEndpoints();
});
