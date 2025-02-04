import React, { useState, useEffect } from "react";
import { getActiveEmulations } from "../services/dashboardService";

const ActiveEmulations = () => {
    const [emulations, setEmulations] = useState([]);
    const [filter, setFilter] = useState("");

    // Fetch emulations once on mount
    useEffect(() => {
        fetchEmulations();
    }, []);

    const fetchEmulations = () => {
        getActiveEmulations()
            .then(setEmulations)
            .catch((error) => console.error("Error fetching emulations:", error));
    };

    const handleFilterChange = (e) => setFilter(e.target.value);

    // Prevents crashes by filtering out null/undefined values
    const filteredEmulations = emulations.filter((emulation) =>
        Object.values(emulation)
            .filter(value => value !== null && typeof value !== "object")
            .some((value) => value.toString().toLowerCase().includes(filter.toLowerCase()))
    );

    return (
        <div style={{ maxHeight: "200px", overflowY: "scroll", background: "#fff", padding: "10px" }}>
            <h3>Active Emulations</h3>

            {/* Filter & Refresh Button */}
            <input
                type="text"
                placeholder="Filter..."
                value={filter}
                onChange={handleFilterChange}
                style={{ marginBottom: "10px" }}
            />
            <button onClick={fetchEmulations} style={{ marginLeft: "10px" }}>Refresh</button>

            {/* Table for Displaying Active Emulations */}
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Status</th>
                        <th>Type</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredEmulations.length > 0 ? (
                        filteredEmulations.map((emulation, idx) => (
                            <tr key={idx}>
                                <td>{emulation.name}</td>
                                <td>{emulation.status}</td>
                                <td>{emulation.type}</td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan="3" style={{ textAlign: "center" }}>No emulations found</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );
};

export default ActiveEmulations;
