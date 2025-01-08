document.addEventListener("DOMContentLoaded", () => {
    const saveConfigButton = document.getElementById("save-configuration");
    const savedConfigurationsList = document.getElementById("saved-configurations-list");

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

    // Initial load of configurations
    loadConfigurations();
});
