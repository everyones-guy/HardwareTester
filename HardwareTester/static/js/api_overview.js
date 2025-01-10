document.addEventListener("DOMContentLoaded", () => {
    const apiTestForm = document.getElementById("api-test-form");
    const responsePreview = document.getElementById("response-preview");

    // Handle API Test Form Submission
    apiTestForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        // Get input values
        const endpoint = document.getElementById("endpoint").value;
        const paramsInput = document.getElementById("params").value;
        let params = {};

        try {
            if (paramsInput.trim()) {
                params = JSON.parse(paramsInput);
            }
        } catch (error) {
            responsePreview.textContent = "Invalid JSON in parameters. Please check your input.";
            responsePreview.style.color = "red";
            return;
        }

        // Determine request method based on endpoint
        const method = endpoint.includes("fetch") || endpoint.includes("list") ? "GET" : "POST";

        // Construct fetch options
        const fetchOptions = {
            method,
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
            },
        };

        if (method === "POST") {
            fetchOptions.body = JSON.stringify(params);
        }

        // Send API request
        try {
            const response = await fetch(endpoint + (method === "GET" && params ? `?${new URLSearchParams(params).toString()}` : ""), fetchOptions);

            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const data = await response.json();
            responsePreview.textContent = JSON.stringify(data, null, 4);
            responsePreview.style.color = "black";
        } catch (error) {
            responsePreview.textContent = `Error: ${error.message}`;
            responsePreview.style.color = "red";
        }
    });
});
