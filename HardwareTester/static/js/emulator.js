$(document).ready(function () {
    const machine = {
        id: "Machine1",
        name: "Test Machine",
        state: "idle",
        peripherals: [],
    };

    const peripheralContainer = $("#peripheral-container");
    const peripheralTemplate = $("#peripheral-template").html();

    // Add a new peripheral to the machine
    $("#add-peripheral").click(function () {
        const peripheralName = prompt("Enter peripheral name (e.g., Temperature Sensor):");
        if (peripheralName) {
            const newPeripheral = createPeripheral(peripheralName);
            machine.peripherals.push(newPeripheral);
            updateMachineView();
        }
    });

    // Create a peripheral with default properties
    function createPeripheral(name) {
        return {
            id: `Peripheral${machine.peripherals.length + 1}`,
            name: name,
            properties: [],
            addProperty(propertyName, behavior) {
                const property = { name: propertyName, value: "N/A", behavior: behavior || "constant" };
                this.properties.push(property);
                simulatePropertyBehavior(property);
            },
        };
    }

    // Simulate property behavior
    function simulatePropertyBehavior(property) {
        if (property.behavior === "oscillate") {
            let value = Math.random() * 100;
            setInterval(() => {
                value += Math.random() * 2 - 1;
                property.value = value.toFixed(2);
                updateMachineView();
            }, 1000);
        } else if (property.behavior === "alarm") {
            let value = 0;
            const target = Math.random() * 100;
            const increment = Math.random() * 5;
            setInterval(() => {
                if (value < target) {
                    value += increment;
                } else {
                    console.log(`ALARM: ${property.name} exceeded target (${target.toFixed(2)})!`);
                }
                property.value = value.toFixed(2);
                updateMachineView();
            }, 1000);
        }
    }

    // Update the machine view in the UI
    function updateMachineView() {
        peripheralContainer.empty();
        machine.peripherals.forEach((peripheral) => {
            const peripheralElement = $(peripheralTemplate).clone();
            peripheralElement.find(".peripheral-name").text(peripheral.name);
            const propertyList = peripheralElement.find(".property-list");

            // Add properties to the peripheral
            peripheral.properties.forEach((property) => {
                propertyList.append(
                    `<li>${property.name}: <span class="property-value">${property.value}</span></li>`
                );
            });

            // Add the property behavior dynamically
            peripheralElement.find(".add-property").click(function () {
                const propertyName = prompt("Enter property name (e.g., pH, pressure):");
                const behavior = prompt("Enter behavior (e.g., constant, oscillate, alarm):", "constant");
                if (propertyName) {
                    peripheral.addProperty(propertyName, behavior);
                }
            });

            peripheralContainer.append(peripheralElement);
        });
    }

    // Simulate machine-wide actions
    function simulateMachineActions() {
        setInterval(() => {
            const state = Math.random() > 0.5 ? "idle" : "active";
            machine.state = state;
            console.log(`Machine state updated: ${machine.state}`);
        }, 5000);
    }

    // Initialize the emulator
    function initializeEmulator() {
        const defaultPeripheral = createPeripheral("Default Sensor");
        defaultPeripheral.addProperty("temperature", "oscillate");
        defaultPeripheral.addProperty("pressure", "constant");
        machine.peripherals.push(defaultPeripheral);

        simulateMachineActions();
        updateMachineView();
    }

    initializeEmulator();
});
