
$(document).ready(function () {
    const canvas = $("#canvas-container");
    const socket = io();

    // Function to add a valve or peripheral visually
    function addComponent(id, type, x = 50, y = 50) {
        const element = $(`<div id="component-${id}" class="draggable"
                    data-id="${id}" data-type="${type}"
                    style="position: absolute; left: ${x}px; top: ${y}px;">
                    <div class="component-body p-2 text-white bg-primary rounded">${type}</div>
                </div>`);
        canvas.append(element);
        enableDrag(element);
    }

    // Real-time updates using Socket.IO
    socket.on("valve_update", (data) => {
        const { id, state, value } = data; // state: 'open', 'closed', 'flow'
        const component = $(`#component-${id}`);
        if (component.length) {
            animateValve(component, state, value);
        }
    });

    // Function to animate valves
    function animateValve(element, state, value) {
        if (state === "open") {
            anime({
                targets: element[0],
                scale: 1.2,
                duration: 800,
                direction: "alternate",
                easing: "easeInOutQuad",
            });
            element.find(".component-body").text(`Valve Open (${value}%)`);
        } else if (state === "closed") {
            anime({
                targets: element[0],
                scale: 1.0,
                duration: 800,
                easing: "easeInOutQuad",
            });
            element.find(".component-body").text("Valve Closed");
        } else if (state === "flow") {
            anime({
                targets: element[0],
                rotate: 360,
                duration: 1000,
                easing: "linear",
                loop: true,
            });
            element.find(".component-body").text(`Flow: ${value} L/s`);
        }
    }

    // Drag-and-drop functionality
    function enableDrag(element) {
        interact(element[0]).draggable({
            listeners: {
                move(event) {
                    const target = event.target;
                    const x = (parseFloat(target.getAttribute("data-x")) || 0) + event.dx;
                    const y = (parseFloat(target.getAttribute("data-y")) || 0) + event.dy;

                    // Restrict movement to canvas bounds
                    if (x >= 0 && y >= 0 && x <= canvas.width() - 100 && y <= canvas.height() - 50) {
                        target.style.transform = `translate(${x}px, ${y}px)`;
                        target.setAttribute("data-x", x);
                        target.setAttribute("data-y", y);
                    }
                },
            },
        });
    }

    // Save Configuration
    $("#save-config").click(function () {
        const layout = [];
        $(".draggable").each(function () {
            const id = $(this).data("id");
            const type = $(this).data("type");
            const x = $(this).position().left;
            const y = $(this).position().top;
            layout.push({ id, type, x, y });
        });

        $.post("/save-configuration", { layout: JSON.stringify(layout) }, function (response) {
            alert(response.message);
        }).fail(() => alert("Failed to save configuration."));
    });


    // Load Configuration
    $("#load-config").click(function () {
        $.get("/load-configuration", function (data) {
            if (data.success) {
                canvas.empty();
                data.layout.forEach(item => addComponent(item.id, item.type, item.x, item.y));
            } else {
                alert(data.error || "Failed to load configuration.");
            }
        }).fail(() => alert("Failed to load configuration."));
    });

    // Add initial components for demo
    addComponent(1, "Valve");
    addComponent(2, "Temperature Sensor", 200, 200);


    socket.on("peripheral_update", (data) => {
        const peripheral = $(`.peripheral-node:contains('${data.name}')`);
        if (peripheral.length) {
            peripheral.find(`.property-value:contains('${data.property}')`).text(data.value);
        }
    });

    // Overview section (placeholder for future enhancements)
    function loadOverview() {
        console.log("Overview section loaded.");
    }

    // Load emulators
    function loadEmulators() {
        $.get("/emulators/list", function (data) {
            const list = $("#emulator-list");
            list.empty();
            if (data.success) {
                data.emulators.forEach((emulator) => {
                    list.append(`
                    <li class="list-group-item">
                        <strong>${emulator.name}</strong> - Status: ${emulator.status}
                        <button class="btn btn-danger btn-sm float-end stop-emulator" data-id="${emulator.id}">Stop</button>
                    </li>
                `);
                });
            } else {
                list.append(`<li class="list-group-item text-danger">Error loading emulators.</li>`);
            }
        });
    }

    // Stop emulator
    $(document).on("click", ".stop-emulator", function () {
        const id = $(this).data("id");
        $.post(`/emulators/stop/${id}`, function (data) {
            if (data.success) {
                alert("Emulator stopped.");
                loadEmulators();
            } else {
                alert("Failed to stop emulator.");
            }
        });
    });

    // Load logs
    function loadLogs() {
        $.get("/logs/recent", function (data) {
            const container = $("#log-output");
            container.empty();
            if (data.success) {
                data.logs.forEach((log) => {
                    container.append(`<p>${log}</p>`);
                });
            } else {
                container.append("<p>Error loading logs.</p>");
            }
        });
    }

    // Load settings
    function loadSettings() {
        $.get("/settings/global", function (data) {
            const list = $("#global-settings-list");
            list.empty();
            if (data.success) {
                data.settings.forEach((setting) => {
                    list.append(`
                    <li class="list-group-item">
                        <strong>${setting.key}</strong>: ${JSON.stringify(setting.value)}
                    </li>
                `);
                });
            } else {
                list.append("<li class="list - group - item text - danger">Error loading settings.</li>");
            }
        });
    }

    // Update global setting
    $("#update-global-setting-form").on("submit", function (event) {
        event.preventDefault();
        const key = $("#setting-key").val();
        const value = $("#setting-value").val();

        $.post("/settings/global", { key, value }, function (data) {
            if (data.success) {
                alert("Setting updated.");
                loadSettings();
            } else {
                alert("Error updating setting.");
            }
        });
    });

    // Initialize dashboard functionality
    $(document).ready(function () {
        loadOverview();
        loadEmulators();
        loadLogs();
        loadSettings();
    });
});

