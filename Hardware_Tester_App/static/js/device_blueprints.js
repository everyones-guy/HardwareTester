$(document).ready(function () {
    const uploadForm = $("#upload-blueprint-form");
    const blueprintFileInput = $("#blueprintFile");
    const blueprintsList = $("#blueprints-list");
    const blueprintsEmptyMessage = $("#blueprints-empty");
    const blueprintPreviewModal = new bootstrap.Modal($("#blueprintPreviewModal")[0]);
    const blueprintPreviewFrame = $("#blueprintPreviewFrame");

    // Fetch and display blueprints on page load
    fetchBlueprints();

    /**
     * Utility: Show alerts for user feedback.
     */
    function showAlert(message, isError = false) {
        alert(isError ? `Error: ${message}` : message);
    }

    /**
     * Handle blueprint upload.
     */
    uploadForm.on("submit", async function (e) {
        e.preventDefault();

        const file = blueprintFileInput[0].files[0];
        if (!file) {
            showAlert("Please select a file to upload.", true);
            return;
        }

        const formData = new FormData();
        formData.append("blueprintFile", file);

        try {
            const data = await apiCall("/blueprints/upload", "POST", formData, true); // Handles FormData properly
            if (data.success) {
                showAlert("Blueprint uploaded successfully!");
                fetchBlueprints();
            } else {
                showAlert(data.error || "Failed to upload blueprint.", true);
            }
        } catch (error) {
            console.error("Error uploading blueprint:", error);
            showAlert("An error occurred while uploading the blueprint.", true);
        }
    });

    /**
     * Fetch blueprints from the server.
     */
    async function fetchBlueprints() {
        try {
            const data = await apiCall("/blueprints", "GET");

            blueprintsList.empty();

            if (data.success && data.blueprints.length > 0) {
                blueprintsEmptyMessage.hide();
                data.blueprints.forEach((blueprint) => {
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
                blueprintsEmptyMessage.show().text("No blueprints available. Upload a blueprint to get started.");
            }
        } catch (error) {
            console.error("Error fetching blueprints:", error);
            showAlert("Failed to load blueprints.", true);
        }
    }

    /**
     * Preview a blueprint.
     */
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

    /**
     * Delete a blueprint.
     */
    $(document).on("click", ".delete-blueprint", async function () {
        const id = $(this).data("id");

        if (!confirm("Are you sure you want to delete this blueprint?")) return;

        try {
            const data = await apiCall(`/blueprints/delete/${id}`, "DELETE");
            if (data.success) {
                showAlert("Blueprint deleted successfully!");
                fetchBlueprints();
            } else {
                showAlert(data.error || "Failed to delete blueprint.", true);
            }
        } catch (error) {
            console.error("Error deleting blueprint:", error);
            showAlert("An error occurred while deleting the blueprint.", true);
        }
    });

    /**
     * Reset form and clear file input on modal close.
     */
    $("#uploadBlueprintModal").on("hidden.bs.modal", function () {
        uploadForm[0].reset();
    });
});
