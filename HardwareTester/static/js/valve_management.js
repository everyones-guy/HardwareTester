
document.addEventListener("DOMContentLoaded", () => {
    const valveList = document.getElementById("valve-list");
    const addValveBtn = document.getElementById("add-valve-btn");

    // Fetch and display valves
    function fetchValves() {
        fetch("/valves/list")
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    valveList.innerHTML = "";
                    data.valves.forEach(valve => {
                        const li = document.createElement("li");
                        li.className = "list-group-item";
                        li.innerHTML = `
                            <strong>${valve.name}</strong> (${valve.type})
                            <button class="btn btn-danger btn-sm float-end delete-valve-btn" data-id="${valve.id}">Delete</button>
                        `;
                        valveList.appendChild(li);
                    });
                }
            });
    }

    // Add a new valve
    addValveBtn.addEventListener("click", () => {
        const name = prompt("Enter valve name:");
        const type = prompt("Enter valve type:");
        if (name && type) {
            fetch("/valves/add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, type })
            }).then(() => fetchValves());
        }
    });

    // Delete a valve
    valveList.addEventListener("click", (e) => {
        if (e.target.classList.contains("delete-valve-btn")) {
            const id = e.target.getAttribute("data-id");
            fetch(`/valves/${id}/delete`, { method: "DELETE" }).then(() => fetchValves());
        }
    });

    fetchValves();
});

