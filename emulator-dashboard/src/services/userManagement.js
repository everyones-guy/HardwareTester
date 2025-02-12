import React, { useState, useEffect } from "react";
import { apiCall } from "../services/apiService"; // API abstraction
import { toast } from "react-toastify"; // Better notifications
import { Modal, Button, Form, Table } from "react-bootstrap"; // UI Framework

const UserManagement = () => {
    const [users, setUsers] = useState([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedUser, setSelectedUser] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [newUser, setNewUser] = useState({ username: "", email: "", role: "Tester" });

    // Fetch users on component mount
    useEffect(() => {
        fetchUsers();
    }, []);

    // Fetch Users from API
    const fetchUsers = async () => {
        try {
            const data = await apiCall("/users/list", "GET");
            if (data.success) {
                setUsers(data.users);
            } else {
                toast.error("Failed to fetch users.");
            }
        } catch (error) {
            console.error("Error fetching users:", error);
            toast.error("Error loading users.");
        }
    };

    // Handle form input changes
    const handleInputChange = (e) => {
        setNewUser({ ...newUser, [e.target.name]: e.target.value });
    };

    // Add User
    const handleAddUser = async (e) => {
        e.preventDefault();
        try {
            const response = await apiCall("/users/add", "POST", newUser);
            if (response.success) {
                toast.success("User added successfully!");
                fetchUsers();
                setShowModal(false);
                setNewUser({ username: "", email: "", role: "Tester" });
            } else {
                toast.error(response.error || "Failed to add user.");
            }
        } catch (error) {
            console.error("Error adding user:", error);
            toast.error("Error adding user.");
        }
    };

    // Delete User
    const handleDeleteUser = async (userId) => {
        if (!window.confirm("Are you sure you want to delete this user?")) return;

        try {
            const response = await apiCall(`/users/delete/${userId}`, "DELETE");
            if (response.success) {
                toast.success("User deleted successfully!");
                fetchUsers();
            } else {
                toast.error("Failed to delete user.");
            }
        } catch (error) {
            console.error("Error deleting user:", error);
            toast.error("Error deleting user.");
        }
    };

    // Edit User Inline
    const handleEditUser = (user) => {
        setSelectedUser(user);
        setShowModal(true);
    };

    // Update User
    const handleUpdateUser = async (e) => {
        e.preventDefault();
        try {
            const response = await apiCall(`/users/update/${selectedUser.id}`, "POST", selectedUser);
            if (response.success) {
                toast.success("User updated successfully!");
                fetchUsers();
                setShowModal(false);
                setSelectedUser(null);
            } else {
                toast.error(response.error || "Failed to update user.");
            }
        } catch (error) {
            console.error("Error updating user:", error);
            toast.error("Error updating user.");
        }
    };

    // Filter Users
    const filteredUsers = users.filter(user =>
        user.username.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase())
    );

    return (
        <div className="container">
            <h2>User Management</h2>

            {/* Search Bar */}
            <input
                type="text"
                className="form-control mb-3"
                placeholder="Search users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
            />

            {/* User Table */}
            <Table striped bordered hover>
                <thead>
                    <tr>
                        <th>Username</th>
                        <th>Email</th>
                        <th>Role</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {filteredUsers.length > 0 ? (
                        filteredUsers.map((user) => (
                            <tr key={user.id}>
                                <td>{user.username}</td>
                                <td>{user.email}</td>
                                <td>{user.role}</td>
                                <td>
                                    <Button variant="warning" size="sm" onClick={() => handleEditUser(user)}>Edit</Button>{" "}
                                    <Button variant="danger" size="sm" onClick={() => handleDeleteUser(user.id)}>Delete</Button>
                                </td>
                            </tr>
                        ))
                    ) : (
                        <tr>
                            <td colSpan="4" className="text-center">No users found.</td>
                        </tr>
                    )}
                </tbody>
            </Table>

            {/* Add User Button */}
            <Button variant="primary" onClick={() => setShowModal(true)}>Add User</Button>

            {/* User Modal */}
            <Modal show={showModal} onHide={() => setShowModal(false)}>
                <Modal.Header closeButton>
                    <Modal.Title>{selectedUser ? "Edit User" : "Add User"}</Modal.Title>
                </Modal.Header>
                <Modal.Body>
                    <Form onSubmit={selectedUser ? handleUpdateUser : handleAddUser}>
                        <Form.Group className="mb-3">
                            <Form.Label>Username</Form.Label>
                            <Form.Control
                                type="text"
                                name="username"
                                value={selectedUser ? selectedUser.username : newUser.username}
                                onChange={selectedUser ? (e) => setSelectedUser({ ...selectedUser, username: e.target.value }) : handleInputChange}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Email</Form.Label>
                            <Form.Control
                                type="email"
                                name="email"
                                value={selectedUser ? selectedUser.email : newUser.email}
                                onChange={selectedUser ? (e) => setSelectedUser({ ...selectedUser, email: e.target.value }) : handleInputChange}
                                required
                            />
                        </Form.Group>

                        <Form.Group className="mb-3">
                            <Form.Label>Role</Form.Label>
                            <Form.Select
                                name="role"
                                value={selectedUser ? selectedUser.role : newUser.role}
                                onChange={selectedUser ? (e) => setSelectedUser({ ...selectedUser, role: e.target.value }) : handleInputChange}
                            >
                                <option value="Admin">Admin</option>
                                <option value="Tester">Tester</option>
                                <option value="Viewer">Viewer</option>
                            </Form.Select>
                        </Form.Group>

                        <Button variant="primary" type="submit">
                            {selectedUser ? "Update User" : "Add User"}
                        </Button>
                    </Form>
                </Modal.Body>
            </Modal>
        </div>
    );
};

export default UserManagement;
