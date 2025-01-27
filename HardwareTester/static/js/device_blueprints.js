$(document).ready(function () {
    const uploadForm = $("#upload-blueprint-form");
    const blueprintFileInput = $("#blueprintFile");
    const blueprintsList = $("#blueprints-list");
    const blueprintsEmptyMessage = $("#blueprints-empty");
    const blueprintPreviewModal = new bootstrap.Modal($("#blueprintPreviewModal")[0]);
    const blueprintPreviewFrame = $("#blueprintPreviewFrame");

    // Fetch and display blueprints on page load
    fetchBlueprints();

    // Utility: Show alerts
    function showAlert(message, isError = false) {
        alert(isError ? `Error: ${message}` : message);
    }

    // Handle blueprint upload
    uploadForm.on("submit", function (e) {
        e.preventDefault();

        const file = blueprintFileInput[0].files[0];
        if (!file) {
            showAlert("Please select a file to upload.", true);
            return;
        }

        const formData = new FormData();
        formData.append("blueprintFile", file);

        $.ajax({
            url: "/blueprints/upload",
            method: "POST",
            processData: false,
            contentType: false,
            data: formData,
            success: function (data) {
                if (data.success) {
                    showAlert("Blueprint uploaded successfully!");
                    fetchBlueprints();
                } else {
                    showAlert(data.error || "Failed to upload blueprint.", true);
                }
            },
            error: function (xhr) {
                console.error("Error uploading blueprint:", xhr);
                showAlert("An error occurred while uploading the blueprint.", true);
            },
        });
    });

    // Fetch blueprints from the server
    function fetchBlueprints() {
        $.ajax({
            url: "/blueprints",
            method: "GET",
            success: function (data) {
                if (data.success && data.blueprints.length > 0) {
                    blueprintsList.empty();
                    blueprintsEmptyMessage.hide();

                    data.blueprints.forEach(function (blueprint) {
                        const listItem = `
                            <li class="list-group-item d-flex justify-content-between align-items-center">
                                <span>${blueprint.name}</span>
                                <div>
                                    <button 
                                        class="btn btn-sm btn-info me-2 preview-blueprint" 
                                        data-url="${blueprint.url}" 
                                        data-name="${blueprint.name}">
                                        Preview
                                    </button>
                                    <button 
                                        class="btn btn-sm btn-danger delete-blueprint" 
                                        data-id="${blueprint.id}">
                                        Delete
                                    </button>
                                </div>
                            </li>`;
                        blueprintsList.append(listItem);
                    });
                } else {
                    blueprintsList.empty();
                    blueprintsEmptyMessage.show().text(
                        "No blueprints available. Upload a blueprint to get started."
                    );
                }
            },
            error: function (xhr) {
                console.error("Error fetching blueprints:", xhr);
                showAlert("Failed to load blueprints.", true);
            },
        });
    }

    // Preview a blueprint
    $(document).on("click", ".preview-blueprint", function () {
        const url = $(this).data("url");
        const name = $(this).data("name");

        if (!url) {
            showAlert("Invalid blueprint URL for preview.", true);
            return;
        }

        blueprintPreviewFrame.attr("src", url);
        $("#blueprintPreviewModalLabel").text(`Preview: ${name}`);
        blueprintPreviewModal.show();
    });

    // Delete a blueprint
    $(document).on("click", ".delete-blueprint", function () {
        const id = $(this).data("id");

        if (!confirm("Are you sure you want to delete this blueprint?")) return;

        $.ajax({
            url: `/blueprints/delete/${id}`,
            method: "DELETE",
            success: function (data) {
                if (data.success) {
                    showAlert("Blueprint deleted successfully!");
                    fetchBlueprints();
                } else {
                    showAlert(data.error || "Failed to delete blueprint.", true);
                }
            },
            error: function (xhr) {
                console.error("Error deleting blueprint:", xhr);
                showAlert("An error occurred while deleting the blueprint.", true);
            },
        });
    });

    // Reset form and clear file input on modal close
    $("#uploadBlueprintModal").on("hidden.bs.modal", function () {
        uploadForm[0].reset();
    });
});
