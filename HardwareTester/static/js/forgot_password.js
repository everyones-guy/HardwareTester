document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("forgot-password-form");

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        event.stopPropagation();

        if (!form.checkValidity()) {
            form.classList.add("was-validated");
            return;
        }

        const email = document.getElementById("email").value;

        fetch("/auth/forgot-password", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": document.querySelector('meta[name="csrf-token"]').getAttribute("content"),
            },
            body: JSON.stringify({ email: email }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    const modal = new bootstrap.Modal(document.getElementById("success-modal"));
                    modal.show();
                    form.reset();
                    form.classList.remove("was-validated");
                } else {
                    alert("Error: " + (data.message || "Unable to send reset email."));
                }
            })
            .catch((error) => {
                console.error("Error sending reset email:", error);
                alert("An unexpected error occurred. Please try again later.");
            });
    });
});
