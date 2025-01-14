$(document).ready(function () {
    const canvas = $("#canvas-container");
    const socket = io();

    // ========== Real-Time Updates ==========
    // Listen for valve updates via Socket.IO
    socket.on("valve_update", (data) => {
        const { id, state, value } = data; // state: 'open', 'closed', 'flow'
        const component = $(`#component-${id}`);
        if (component.length) {
            animateValve(component, state, value);
        }
    });

    // Listen for peripheral updates
    socket.on("peripheral_update", (data) => {
        const peripheral = $(`.peripheral-node:contains('${data.name}')`);
        if (peripheral.length) {
            peripheral.find(`.property-value:contains('${data.property}')`).text(data.value);
        }
    });

    // ========== Valve Animation ==========
    function animateValve(element, state, value) {
        const animationConfig = {
            targets: element[0],
            easing: "easeInOutQuad",
            duration: 800,
        };

        switch (state) {
            case "open":
                animationConfig.scale = 1.2;
                animationConfig.direction = "alternate";
                element.find(".component-body").text(`Valve Open (${value}%)`);
                break;
            case "closed":
                animationConfig.scale = 1.0;
                element.find(".component-body").text("Valve Closed");
                break;
            case "flow":
                animationConfig.rotate = 360;
                animationConfig.duration = 1000;
                animationConfig.loop = true;
                element.find(".component-body").text(`Flow: ${value} L/s`);
                break;
        }

        anime(animationConfig);
    }

    // ========== Drag-and-Drop ==========
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

    // ========== Save & Load Configuration ==========
    $("#save-config").click(function () {
        const layout = $(".draggable").map((_, element) => ({
            id: $(element).data("id"),
            type: $(element).data("type"),
            x: $(element).position().left,
            y: $(element).position().top,
        })).get();

        $.post("/save-configuration", { layout: JSON.stringify(layout) }, function (response) {
            alert(response.message);
        }).fail(() => alert("Failed to save configuration."));
    });

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

    // ========== User Management ==========
    function loadUserManagement() {
        const userList = $("#user-management-list");
        userList.empty().append("<li>Loading...</li>");
        $.getJSON("/users/list", function (data) {
            userList.empty();
            if (data.success) {
                data.users.forEach(user => {
                    userList.append(`
                    <li class="list-group-item">
                        <strong>${user.username}</strong> - ${user.email}
                        <button class="btn btn-sm btn-danger float-end" onclick="deleteUser(${user.id})">Delete</button>
                    </li>
                `);
                });
            } else {
                userList.append(`<li class="list-group-item text-danger">${data.error}</li>`);
            }
        }).fail(() => {
            userList.empty().append("<li class='list-group-item text-danger'>Failed to load users.</li>");
        });
    }

    function deleteUser(userId) {
        if (confirm("Are you sure you want to delete this user?")) {
            $.ajax({
                url: `/users/delete/${userId}`,
                type: "DELETE",
                success: function (response) {
                    if (response.success) {
                        alert(response.message);
                        loadUserManagement();
                    } else {
                        alert(`Error: ${response.error}`);
                    }
                },
                error: function () {
                    alert("Failed to delete user.");
                },
            });
        }
    }

    $("#add-user-form").on("submit", function (event) {
        event.preventDefault();
        const payload = Object.fromEntries(new FormData(this));

        $.ajax({
            url: "/users/add",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify(payload),
            success: function (response) {
                if (response.success) {
                    alert(response.message);
                    loadUserManagement();
                } else {
                    alert(`Error: ${response.error}`);
                }
            },
            error: function () {
                alert("Failed to add user.");
            },
        });
    });

    $("#user-management-tab").on("click", loadUserManagement);

    // ========== Initialize ==========
    loadOverview();
    loadEmulators();
    loadLogs();
    loadSettings();
});
