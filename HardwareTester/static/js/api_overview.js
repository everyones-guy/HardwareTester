document.addEventListener("DOMContentLoaded", () => {
    const apiTestForm = document.getElementById("api-test-form");
    const responsePreview = document.getElementById("response-preview");

    // Handle API Test Form Submission
    apiTestForm.addEventListener("submit", (event) => {
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
            responsePreview.textContent = "Invalid JSON in parameters.";
            return;
        }

        // Send API request
        fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').content,
            },
            body: JSON.stringify(params),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                responsePreview.textContent = JSON.stringify(data, null, 4);
            })
            .catch((error) => {
                responsePreview.textContent = `Error: ${error.message}`;
            });
    });
});
