
// Fetch and display test plans
function loadTestPlans() {
    $.getJSON("/test-plans/list", function (data) {
        const list = $("#test-plans-list");
        list.empty();
        if (data.success) {
            data.testPlans.forEach((plan) => {
                list.append(
                    `<li class="list-group-item">
                        <strong>${plan.name}</strong> - Uploaded by ${plan.uploaded_by}
                        <button class="btn btn-sm btn-primary float-end" onclick="runTestPlan(${plan.id})">Run</button>
                    </li>`
                );
            });
        } else {
            list.append(`<li class="list-group-item text-danger">${data.error}</li>`);
        }
    });
}

// Handle test plan upload
function handleUploadForm() {
    $("#upload-test-plan-form").on("submit", function (event) {
        event.preventDefault();
        const formData = new FormData(this);
        $.ajax({
            url: "/test-plans/upload",
            type: "POST",
            headers: {
                "X-CSRFToken": $('meta[name="csrf-token"]').attr('content')  // Ensure CSRF token is sent
            },
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.success) {
                    alert(response.message);
                    loadTestPlans();
                } else {
                    alert(`Error: ${response.error}`);
                }
            },
        });
    });
}

// Run a test plan
function runTestPlan(testPlanId) {
    $.post(`/test-plans/run/${testPlanId}`, function (data) {
        const results = $("#test-results");
        results.empty();
        if (data.success) {
            let resultHTML = "<ul>";
            data.results.forEach((result) => {
                resultHTML += `<li>${result.step.Step}: ${result.result}</li>`;
            });
            resultHTML += "</ul>";
            results.html(resultHTML);
        } else {
            results.html(`<p class="text-danger">${data.error}</p>`);
        }
    });
}

// Initialize scripts
$(document).ready(function () {
    loadTestPlans();
    handleUploadForm();
});



