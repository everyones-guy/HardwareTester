document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("forgot-password-form");

    form.addEventListener("submit", async (event) => {
        event.preventDefault();
        event.stopPropagation();

        if (!form.checkValidity()) {
            form.classList.add("was-validated");
            return;
        }

        const email = document.getElementById("email").value;

        try {
            const data = await apiCall("/auth/forgot-password", "POST", { email });

            if (data.success) {
                const modal = new bootstrap.Modal(document.getElementById("success-modal"));
                modal.show();
                form.reset();
                form.classList.remove("was-validated");
            } else {
                showAlert(data.message || "Unable to send reset email.", true);
            }
        } catch (error) {
            console.error("Error sending reset email:", error);
            showAlert("An unexpected error occurred. Please try again later.", true);
        }
    });

    /**
     * Utility: Show alert messages
     */
    function showAlert(message, isError = false) {
        alert(isError ? `Error: ${message}` : message);
    }
});
