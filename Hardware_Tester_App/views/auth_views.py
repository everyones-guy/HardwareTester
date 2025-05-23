from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from Hardware_Tester_App.extensions import db
from Hardware_Tester_App.utils.bcrypt_utils import check_password, hash_password
from Hardware_Tester_App.models.user_models import User
from Hardware_Tester_App.forms import LoginForm, RegistrationForm, ProfileForm
from sqlalchemy.exc import IntegrityError
from Hardware_Tester_App.utils.custom_logger import CustomLogger

# Initialize logger
logger = CustomLogger.get_logger("auth_views")

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password(form.password.data, user.password_hash):  # Validate password
            login_user(user)  # Log the user in
            logger.info(f"User {user.email} logged in successfully.")
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.dashboard'))
        logger.warning(f"Failed login attempt for email: {form.email.data}")
        flash('Invalid credentials.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logger.info(f"User {current_user.email} logged out.")
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = hash_password(form.password.data)  # Use bcrypt_utils.hash_password
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            logger.info(f"User {user.email} registered successfully.")
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"An error occurred during registration: {e}")
            if "UNIQUE constraint failed: users.email" in str(e):
                flash('Email already exists.', 'danger')
            elif "UNIQUE constraint failed: users.username" in str(e):
                flash('Username already exists.', 'danger')
            else:
                flash('An error occurred. Please try again.', 'danger')
    return render_template('auth/register.html', form=form)


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm(obj=current_user)
    if form.validate_on_submit():
        try:
            current_user.name = form.name.data
            current_user.email = form.email.data
            db.session.commit()
            logger.info(f"User {current_user.email} updated their profile successfully.")
            flash("Profile updated successfully.", "success")
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"An error occurred while updating profile for {current_user.email}: {e}")
            flash("An error occurred while updating your profile. Please try again.", "danger")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", form=form, user=current_user)
