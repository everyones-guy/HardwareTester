document.addEventListener("DOMContentLoaded", () => {
    const saveForm = document.getElementById("save-configuration-form");
    const savedList = document.getElementById("saved-configurations-list");
    const previewCard = document.getElementById("configuration-preview-card");
    const previewContent = document.getElementById("configuration-preview");
    const applyButton = document.getElementById("apply-configuration");
    const discardButton = document.getElementById("discard-preview");
    const saveConfigButton = document.getElementById("save-configuration");
    const savedConfigurationsList = document.getElementById("saved-configurations-list");


    // Fetch saved configurations
    function fetchConfigurations() {
        fetch("/configurations/list")
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    savedList.innerHTML = "";
                    data.configurations.forEach((config) => {
                        const listItem = document.createElement("li");
                        listItem.className = "list-group-item d-flex justify-content-between align-items-center";
                        listItem.innerHTML = `
                            <span>${config.name}</span>
                            <div>
                                <button class="btn btn-sm btn-primary" onclick="previewConfiguration(${config.id})">Preview</button>
                            </div>
                        `;
                        savedList.appendChild(listItem);
                    });
                } else {
                    savedList.innerHTML = `<li class="list-group-item text-danger">${data.error}</li>`;
                }
            })
            .catch((error) => console.error("Error fetching configurations:", error));
    }
    // Save current configuration
    saveConfigButton.addEventListener("click", () => {
        fetch("/save-configuration", { method: "POST" })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("Configuration saved successfully!");
                    loadConfigurations();
                } else {
                    alert("Error saving configuration: " + data.message);
                }
            })
            .catch(error => console.error("Error saving configuration:", error));
    });

    // Load configurations into the list
    function loadConfigurations() {
        fetch("/get-configurations")
            .then(response => response.json())
            .then(data => {
                savedConfigurationsList.innerHTML = ""; // Clear list
                if (data.success) {
                    data.configurations.forEach(config => {
                        const listItem = document.createElement("li");
                        listItem.className = "list-group-item d-flex justify-content-between align-items-center";
                        listItem.innerHTML = `
                            <strong>${config.name}</strong>
                            <button class="btn btn-primary btn-sm" data-id="${config.id}">Load</button>
                        `;
                        listItem.querySelector("button").addEventListener("click", () => loadConfiguration(config.id));
                        savedConfigurationsList.appendChild(listItem);
                    });
                } else {
                    const errorItem = document.createElement("li");
                    errorItem.className = "list-group-item text-danger";
                    errorItem.textContent = "Error loading configurations.";
                    savedConfigurationsList.appendChild(errorItem);
                }
            })
            .catch(error => console.error("Error fetching configurations:", error));
    }

    // Load a specific configuration
    function loadConfiguration(id) {
        fetch(`/load-configuration/${id}`)
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert("Configuration loaded successfully!");
                } else {
                    alert("Error loading configuration: " + data.message);
                }
            })
            .catch(error => console.error("Error loading configuration:", error));
    }

    // Save configuration
    saveForm.addEventListener("submit", (event) => {
        event.preventDefault();
        const name = document.getElementById("configuration-name").value;

        fetch("/configurations/save", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector("meta[name='csrf-token']").content,
            },
            body: JSON.stringify({ name, layout: {} }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    alert(data.message);
                    saveForm.reset();
                    fetchConfigurations();
                } else {
                    alert(`Error: ${data.error}`);
                }
            })
            .catch((error) => console.error("Error saving configuration:", error));
    });

    // Preview configuration
    window.previewConfiguration = (id) => {
        fetch(`/configurations/preview/${id}`)
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    previewContent.innerHTML = data.preview;
                    previewCard.classList.remove("d-none");
                } else {
                    alert(`Error: ${data.error}`);
                }
            })
            .catch((error) => console.error("Error fetching preview:", error));
    };

    // Discard preview
    discardButton.addEventListener("click", () => {
        previewCard.classList.add("d-none");
        previewContent.innerHTML = "";
    });

    // Apply configuration (mock)
    applyButton.addEventListener("click", () => {
        alert("Configuration applied successfully.");
        discardButton.click();
    });

    // Initialize
    fetchConfigurations();
});
