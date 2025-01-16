$(document).ready(function () {
    const uploadForm = $("#upload-blueprint-form");
    const blueprintFileInput = $("#blueprintFile");
    const blueprintsList = $("#blueprints-list");
    const blueprintsEmptyMessage = $("#blueprints-empty");
    const blueprintPreviewModal = new bootstrap.Modal($("#blueprintPreviewModal")[0]);
    const blueprintPreviewFrame = $("#blueprintPreviewFrame");

    // Fetch and display blueprints on page load
    fetchBlueprints();

    // Handle blueprint upload
    uploadForm.on("submit", function (e) {
        e.preventDefault();
        const formData = new FormData();
        const file = blueprintFileInput[0].files[0];

        if (!file) {
            alert("Please select a file to upload.");
            return;
        }

        formData.append("blueprintFile", file);

        $.ajax({
            url: "/blueprints/upload",
            method: "POST",
            processData: false,
            contentType: false,
            data: formData,
            success: function (data) {
                if (data.success) {
                    alert("Blueprint uploaded successfully!");
                    fetchBlueprints();
                } else {
                    alert(`Error: ${data.error}`);
                }
            },
            error: function (xhr) {
                console.error("Error uploading blueprint:", xhr);
                alert("An error occurred while uploading the blueprint.");
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
                                    <button class="btn btn-sm btn-info me-2 preview-blueprint" data-url="${blueprint.url}" data-name="${blueprint.name}">Preview</button>
                                    <button class="btn btn-sm btn-danger delete-blueprint" data-id="${blueprint.id}">Delete</button>
                                </div>
                            </li>`;
                        blueprintsList.append(listItem);
                    });
                } else {
                    blueprintsList.empty();
                    blueprintsEmptyMessage.show();
                }
            },
            error: function (xhr) {
                console.error("Error fetching blueprints:", xhr);
                alert("Failed to load blueprints.");
            },
        });
    }

    // Preview a blueprint
    $(document).on("click", ".preview-blueprint", function () {
        const url = $(this).data("url");
        const name = $(this).data("name");
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
                    alert("Blueprint deleted successfully!");
                    fetchBlueprints();
                } else {
                    alert(`Error: ${data.error}`);
                }
            },
            error: function (xhr) {
                console.error("Error deleting blueprint:", xhr);
                alert("Failed to delete blueprint.");
            },
        });
    });
});