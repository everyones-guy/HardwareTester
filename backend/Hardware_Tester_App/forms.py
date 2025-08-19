# forms.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileRequired
from wtforms import (
    StringField,
    IntegerField,
    FileField,
    SubmitField,
    TextAreaField,
    PasswordField,
    SelectField,
    BooleanField,
)
from wtforms.validators import (
    DataRequired,
    Length,
    NumberRange,
    Optional,
    Email,
    EqualTo,
    ValidationError,
)
import re


# -----------------------------
# Shared / Custom Validators
# -----------------------------
class PasswordValidator:
    """
    Ensures the password contains at least:
      - 8 chars
      - one uppercase, one lowercase, one digit, one special char (@$!%*?&)
    """
    def __init__(self, message=None):
        self.message = message or (
            "Password must include at least one uppercase letter, one lowercase letter, "
            "one digit, and one special character."
        )
        # Compile once; anchor length check here too
        self._regex = re.compile(
            r"^(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$"
        )

    def __call__(self, form, field):
        password = field.data or ""
        if not self._regex.match(password):
            raise ValidationError(self.message)


# -----------------------------
# Auth
# -----------------------------
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=25, message="Username must be between 3 and 25 characters."),
        ],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(), Email(message="Please enter a valid email address.")],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            PasswordValidator(),
        ],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Register")


class ProfileForm(FlaskForm):
    name = StringField(
        "Name",
        validators=[
            DataRequired(message="Name is required."),
            Length(min=2, max=50, message="Name must be between 2 and 50 characters."),
        ],
    )
    email = StringField(
        "Email",
        validators=[DataRequired(message="Email is required."), Email(message="Invalid email address.")],
    )
    bio = TextAreaField("Bio", validators=[Optional()])
    submit = SubmitField("Update Profile")


# -----------------------------
# Uploads
# -----------------------------
class UploadSpecSheetForm(FlaskForm):
    spec_sheet = FileField(
        "Spec Sheet",
        validators=[
            FileRequired(message="Please upload a spec sheet file."),
            FileAllowed({"pdf", "docx", "xlsx"}, "Allowed file types: PDF, DOCX, XLSX."),
        ],
    )
    device_id = IntegerField(
        "Device ID (Optional)",
        validators=[Optional(), NumberRange(min=1, message="Device ID must be a positive integer.")],
    )
    submit = SubmitField("Upload Spec Sheet")


class UploadTestPlanForm(FlaskForm):
    test_plan_file = FileField(
        "Test Plan File",
        validators=[
            FileRequired(message="Please upload a test plan file."),
            FileAllowed({"pdf", "csv", "txt"}, "Allowed file types: PDF, CSV, TXT."),
        ],
    )
    submit = SubmitField("Upload Test Plan")


# -----------------------------
# Emulation / Test Plans
# -----------------------------
class StartEmulationForm(FlaskForm):
    machine_name = StringField(
        "Machine Name",
        validators=[DataRequired(message="Machine name is required.")],
        render_kw={"class": "form-control", "placeholder": "Enter machine name"},
    )
    blueprint = SelectField(
        "Blueprint",
        choices=[],           # set at runtime: form.blueprint.choices = [...]
        validators=[DataRequired(message="Please select a blueprint.")],
        render_kw={"class": "form-control"},
        coerce=str,
    )
    stress_test = BooleanField("Stress Test", render_kw={"class": "form-check-input"})
    submit = SubmitField("Start Emulation", render_kw={"class": "btn btn-primary"})


class RunTestPlanForm(FlaskForm):
    test_plan_id = IntegerField(
        "Test Plan ID",
        validators=[DataRequired(message="Test Plan ID is required."), NumberRange(min=1, message="Must be positive.")],
    )
    submit = SubmitField("Run Test Plan")


# -----------------------------
# Valves / Devices
# -----------------------------
class AddValveForm(FlaskForm):
    name = StringField(
        "Valve Name",
        validators=[DataRequired(), Length(max=255, message="Name must not exceed 255 characters.")],
    )
    valve_type = StringField(
        "Valve Type",
        validators=[DataRequired(), Length(max=255, message="Type must not exceed 255 characters.")],
    )
    api_endpoint = StringField(
        "API Endpoint (Optional)",
        validators=[Optional()],
        description="Optional URL to a service endpoint (validated in view/service).",
    )
    specifications = TextAreaField("Specifications (Optional)", validators=[Optional()])
    submit = SubmitField("Add Valve")


class AddEmulatorForm(FlaskForm):
    name = StringField("Name", validators=[Optional(), Length(max=255)])
    description = StringField("Description", validators=[Optional(), Length(max=255)])
    json_file = FileField("Upload JSON File", validators=[Optional(), FileAllowed({"json"}, "JSON only.")])
    json_text = TextAreaField("Paste JSON Text", validators=[Optional()])
    submit = SubmitField("Add Emulator")


# -----------------------------
# Settings
# -----------------------------
class SettingsForm(FlaskForm):
    key = StringField("Setting Key", validators=[DataRequired(), Length(min=1, max=255)])
    value = StringField("Setting Value", validators=[DataRequired(), Length(min=1, max=1024)])
    submit = SubmitField("Save Setting")
