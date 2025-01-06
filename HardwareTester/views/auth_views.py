from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from HardwareTester.extensions import db, csrf, login_manager
from HardwareTester.forms import LoginForm, RegistrationForm, ProfileForm
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = db.User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('dashboard.dashboard_home'))
        flash('Invalid credentials.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
        try:
            user = db.User(
                username=form.username.data,
                email=form.email.data,
                password_hash=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except IntegrityError as e:
            db.session.rollback()
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
        current_user.name = form.name.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Profile updated successfully.", "success")
        return redirect(url_for("auth.profile"))
    return render_template("auth/profile.html", form=form)

@login_manager.unauthorized_handler
def unauthorized():
    flash('Please log in to access this page.', 'warning')
    return redirect(url_for("auth.login", next=request.url))

