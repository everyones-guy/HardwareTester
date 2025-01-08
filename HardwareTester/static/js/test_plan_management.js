document.addEventListener("DOMContentLoaded", () => {
    const testPlansList = document.getElementById("test-plans-list");
    const testResults = document.getElementById("test-results");
    const previewSection = document.getElementById("test-plan-preview-section");
    const previewPlanName = document.getElementById("preview-plan-name");
    const previewUploadedBy = document.getElementById("preview-uploaded-by");
    const previewSteps = document.getElementById("preview-steps");
    const runPreviewPlanButton = document.getElementById("run-preview-plan");

    let currentPreviewPlanId = null;

    // Fetch and display test plans
    function loadTestPlans() {
        fetch("/test-plans/list")
            .then((response) => response.json())
            .then((data) => {
                testPlansList.innerHTML = "";
                if (data.success) {
                    data.testPlans.forEach((plan) => {
                        const listItem = document.createElement("li");
                        listItem.className = "list-group-item d-flex justify-content-between align-items-center";
                        listItem.innerHTML = `
                            <div>
                                <strong>${plan.name}</strong> - Uploaded by ${plan.uploaded_by}
                            </div>
                            <button class="btn btn-sm btn-secondary" onclick="previewTestPlan(${plan.id})">Preview</button>
                        `;
                        testPlansList.appendChild(listItem);
                    });
                } else {
                    testPlansList.innerHTML = `<li class="list-group-item text-danger">${data.error}</li>`;
                }
            })
            .catch((error) => console.error("Error loading test plans:", error));
    }

    // Handle test plan upload
    document.getElementById("upload-test-plan-form").addEventListener("submit", (event) => {
        event.preventDefault();
        const formData = new FormData(event.target);
        fetch("/test-plans/upload", {
            method: "POST",
            body: formData,
            headers: {
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').getAttribute("content"),
            },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    alert(data.message);
                    loadTestPlans();
                } else {
                    alert(`Error: ${data.error}`);
                }
            })
            .catch((error) => console.error("Error uploading test plan:", error));
    });

    // Preview a test plan
    window.previewTestPlan = (testPlanId) => {
        fetch(`/test-plans/${testPlanId}/preview`)
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    currentPreviewPlanId = testPlanId;
                    previewPlanName.textContent = data.plan.name;
                    previewUploadedBy.textContent = data.plan.uploaded_by;
                    previewSteps.innerHTML = data.plan.steps
                        .map((step, index) => `<li class="list-group-item">Step ${index + 1}: ${step.description}</li>`)
                        .join("");
                    previewSection.classList.remove("d-none");
                } else {
                    alert(data.error);
                }
            })
            .catch((error) => console.error("Error fetching test plan preview:", error));
    };

    // Run the previewed test plan
    runPreviewPlanButton.addEventListener("click", () => {
        if (currentPreviewPlanId) {
            fetch(`/test-plans/run/${currentPreviewPlanId}`, { method: "POST" })
                .then((response) => response.json())
                .then((data) => {
                    testResults.innerHTML = "";
                    if (data.success) {
                        const resultsHTML = data.results
                            .map((result) => `<li>${result.step.Step}: ${result.result}</li>`)
                            .join("");
                        testResults.innerHTML = `<ul>${resultsHTML}</ul>`;
                    } else {
                        testResults.innerHTML = `<p class="text-danger">${data.error}</p>`;
                    }
                })
                .catch((error) => console.error("Error running test plan:", error));
        }
    });

    // Initial load
    loadTestPlans();
});
