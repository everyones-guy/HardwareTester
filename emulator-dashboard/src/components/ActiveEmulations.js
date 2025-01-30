import React, { useState, useEffect } from "react";
import { getActiveEmulations } from "../services/dashboardService";

const ActiveEmulations = () => {
    const [emulations, setEmulations] = useState([]);
    const [filter, setFilter] = useState("");

    useEffect(() => {
        getActiveEmulations().then(setEmulations);
        getActiveEmulations().then((setEmulations) => setEmulations(setEmulations));

    }, []);

    const handleFilterChange = (e) => setFilter(e.target.value);

    const filteredEmulations = emulations.filter((emulation) =>
        Object.values(emulation).some((value) =>
            value.toString().toLowerCase().includes(filter.toLowerCase())
        )
    );

    return (
        <div style={{ maxHeight: "150px", overflowY: "scroll", background: "#fff", padding: "10px" }}>
            <h3>Active Emulations</h3>
            <input
                type="text"
                placeholder="Filter..."
                value={filter}
                onChange={handleFilterChange}
                style={{ marginBottom: "10px" }}
            />
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredEmulations.map((emulation, idx) => (
                        <tr key={idx}>
                            <td>{emulation.name}</td>
                            <td>{emulation.status}</td>
                            <td>{emulation.type}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default ActiveEmulations;
