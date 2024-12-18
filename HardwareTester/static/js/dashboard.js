$(document).ready(function () {
    const canvas = $("#canvas-container");

    // Save configuration
    $("#save-config").click(function () {
        const layout = [];
        $(".draggable").each(function () {
            const id = $(this).data("id");
            const type = $(this).data("type");
            const x = $(this).position().left;
            const y = $(this).position().top;
            layout.push({ id, type, x, y });
        });

        const configName = prompt("Enter a name for the configuration:");
        if (configName) {
            $.ajax({
                url: "/configurations/",
                type: "POST",
                contentType: "application/json",
                data: JSON.stringify({ name: configName, layout: layout }),
                success: function (response) {
                    alert(response.message);
                },
                error: function (xhr) {
                    const errorMessage = xhr.responseJSON?.error || "An error occurred.";
                    alert(errorMessage);
                },
            });
        }
    });

    // Load configuration
    $("#load-config").click(function () {
        $.get("/configurations/", function (data) {
            if (data.success) {
                const configList = data.configurations;
                const configId = prompt(
                    "Enter configuration ID to load:\n" +
                    configList.map((c) => `${c.id}: ${c.name}`).join("\n")
                );

                if (configId) {
                    $.get(`/configurations/${configId}`, function (response) {
                        if (response.success) {
                            const layout = response.configuration.layout;
                            canvas.empty();
                            layout.forEach((item) => {
                                const element = $(
                                    `<div id="component-${item.id}" class="draggable" 
                                          data-id="${item.id}" data-type="${item.type}" 
                                          style="position: absolute; left: ${item.x}px; top: ${item.y}px;">
                                          <div class="component-body p-2 bg-primary text-white rounded">${item.type}</div>
                                      </div>`
                                );
                                canvas.append(element);
                                enableDrag(element);
                            });
                        }
                    });
                }
            }
        });
    });

    // Enable drag-and-drop for components
    function enableDrag(element) {
        interact(element[0]).draggable({
            listeners: {
                move(event) {
                    const target = event.target;
                    const x = (parseFloat(target.getAttribute("data-x")) || 0) + event.dx;
                    const y = (parseFloat(target.getAttribute("data-y")) || 0) + event.dy;
                    target.style.transform = `translate(${x}px, ${y}px)`;
                    target.setAttribute("data-x", x);
                    target.setAttribute("data-y", y);
                },
            },
        });
    }
});
