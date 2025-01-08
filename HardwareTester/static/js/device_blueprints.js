document.addEventListener("DOMContentLoaded", () => {
    const uploadForm = document.getElementById("upload-blueprint-form");
    const blueprintFileInput = document.getElementById("blueprintFile");
    const blueprintsList = document.getElementById("blueprints-list");
    const blueprintsEmptyMessage = document.getElementById("blueprints-empty");
    const blueprintPreviewModal = new bootstrap.Modal(document.getElementById("blueprintPreviewModal"));
    const blueprintPreviewFrame = document.getElementById("blueprintPreviewFrame");

    // Fetch and display blueprints on page load
    fetchBlueprints();

    // Handle blueprint upload
    uploadForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const formData = new FormData();
        const file = blueprintFileInput.files[0];

        if (!file) {
            alert("Please select a file to upload.");
            return;
        }

        formData.append("blueprintFile", file);

        try {
            const response = await fetch("/blueprints/upload", {
                method: "POST",
                body: formData,
            });

            const data = await response.json();
            if (data.success) {
                alert("Blueprint uploaded successfully!");
                fetchBlueprints();
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error("Error uploading blueprint:", error);
            alert("An error occurred while uploading the blueprint.");
        }
    });

    // Fetch blueprints from the server
    async function fetchBlueprints() {
        try {
            const response = await fetch("/blueprints");
            const data = await response.json();

            if (data.success && data.blueprints.length > 0) {
                blueprintsList.innerHTML = "";
                blueprintsEmptyMessage.style.display = "none";

                data.blueprints.forEach((blueprint) => {
                    const listItem = document.createElement("li");
                    listItem.className = "list-group-item d-flex justify-content-between align-items-center";
                    listItem.innerHTML = `
                        <span>${blueprint.name}</span>
                        <div>
                            <button class="btn btn-sm btn-info me-2" onclick="previewBlueprint('${blueprint.url}', '${blueprint.name}')">Preview</button>
                            <button class="btn btn-sm btn-danger" onclick="deleteBlueprint(${blueprint.id})">Delete</button>
                        </div>
                    `;
                    blueprintsList.appendChild(listItem);
                });
            } else {
                blueprintsList.innerHTML = "";
                blueprintsEmptyMessage.style.display = "block";
            }
        } catch (error) {
            console.error("Error fetching blueprints:", error);
            alert("Failed to load blueprints.");
        }
    }

    // Preview a blueprint
    window.previewBlueprint = (url, name) => {
        blueprintPreviewFrame.src = url;
        document.getElementById("blueprintPreviewModalLabel").innerText = `Preview: ${name}`;
        blueprintPreviewModal.show();
    };

    // Delete a blueprint
    window.deleteBlueprint = async (id) => {
        if (!confirm("Are you sure you want to delete this blueprint?")) return;

        try {
            const response = await fetch(`/blueprints/delete/${id}`, { method: "DELETE" });
            const data = await response.json();

            if (data.success) {
                alert("Blueprint deleted successfully!");
                fetchBlueprints();
            } else {
                alert(`Error: ${data.error}`);
            }
        } catch (error) {
            console.error("Error deleting blueprint:", error);
            alert("Failed to delete blueprint.");
        }
    };
});
