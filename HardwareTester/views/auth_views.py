
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, current_user, login_required, current_user
from HardwareTester.models import User
from HardwareTester.extensions import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from HardwareTester.forms import RegisterForm


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.json or request.form
        email = data.get("email")
        password = data.get("password")

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return jsonify({"success": True, "message": "Logged in successfully."})
        return jsonify({"success": False, "message": "Invalid credentials."}), 401

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard_home"))

    form = RegisterForm()
    if form.validate_on_submit():
        # Check if the user already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash("Email already registered.", "danger")
            return redirect(url_for("auth.register"))

        # Create a new user
        hashed_password = generate_password_hash(form.password.data, method="sha256")
        new_user = User(email=form.email.data, password=hashed_password, role="user") # Assign default role
        db.session.add(new_user)
        db.session.commit()

        # Automatically log in the new user
        login_user(new_user)
        flash("Registration successful! You are now logged in.", "success")
        return redirect(url_for("dashboard.dashboard_home"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        data = request.form
        current_user.name = data.get("name", current_user.name)
        current_user.email = data.get("email", current_user.email)
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", user=current_user)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("auth.login"))

