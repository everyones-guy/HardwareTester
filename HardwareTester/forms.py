from flask_wtf import FlaskForm
from wtforms import (
    StringField, 
    IntegerField, 
    FileField, 
    SubmitField, 
    TextAreaField, 
    PasswordField, 
    SelectField
)
from wtforms.validators import (
    DataRequired, 
    Length, 
    NumberRange, 
    Optional, 
    Regexp, 
    Email, 
    EqualTo
)
from flask_wtf.file import FileAllowed, FileRequired
import re

class UploadSpecSheetForm(FlaskForm):
    spec_sheet = FileField(
        "Spec Sheet",
        validators=[
            FileRequired(message="Please upload a spec sheet file."),
            FileAllowed({"pdf", "docx", "xlsx"}, "Allowed file types: PDF, DOCX, XLSX."),
        ]
    )
    valve_id = IntegerField(
        "Valve ID (Optional)",
        validators=[
            Optional(),
            NumberRange(min=1, message="Valve ID must be a positive integer."),
        ]
    )
    submit = SubmitField("Upload Spec Sheet")

class UploadTestPlanForm(FlaskForm):
    test_plan_file = FileField(
        "Test Plan File",
        validators=[
            FileRequired(message="Please upload a test plan file."),
            FileAllowed({"pdf", "csv", "txt"}, "Allowed file types: PDF, CSV, TXT."),
        ]
    )
    submit = SubmitField("Upload Test Plan")

class AddValveForm(FlaskForm):
    name = StringField(
        "Valve Name",
        validators=[
            DataRequired(message="Valve name is required."),
            Length(max=255, message="Valve name must not exceed 255 characters."),
        ]
    )
    valve_type = StringField(
        "Valve Type",
        validators=[
            DataRequired(message="Valve type is required."),
            Length(max=255, message="Valve type must not exceed 255 characters."),
        ]
    )
    api_endpoint = StringField(
        "API Endpoint (Optional)",
        validators=[
            Optional(),
            Regexp(r'^https?:\/\/.*', message="API Endpoint must be a valid URL."),
        ]
    )
    specifications = TextAreaField(
        "Specifications (Optional)",
        validators=[Optional()]
    )
    submit = SubmitField("Add Valve")

class RunTestPlanForm(FlaskForm):
    test_plan_id = IntegerField(
        "Test Plan ID",
        validators=[
            DataRequired(message="Test Plan ID is required."),
            NumberRange(min=1, message="Test Plan ID must be a positive integer."),
        ]
    )
    submit = SubmitField("Run Test Plan")
    
# Custom password complexity validator
class PasswordComplexity:
    def __init__(self, message=None):
        if not message:
            message = (
                "Password must include at least one uppercase letter, one lowercase letter, "
                "one digit, and one special character."
            )
        self.message = message

    def __call__(self, form, field):
        password = field.data
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$', password):
            raise ValueError(self.message)

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class RegistrationForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=6), PasswordComplexity()],
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    submit = SubmitField("Register")

class ProfileForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Update Profile")

# User Registration Form
class RegisterForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=80, message="Username must be between 3 and 80 characters.")
        ]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            PasswordComplexity(),
            Length(min=8, message="Password must be at least 8 characters long."),
        ]
    )
    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )
    submit = SubmitField("Register")

# User Login Form
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

# Profile Update Form
class ProfileForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    bio = TextAreaField("Bio", validators=[Optional()])
    submit = SubmitField("Update Profile")

# Upload Spec Sheet Form
class UploadSpecSheetForm(FlaskForm):
    spec_sheet = FileField(
        "Spec Sheet",
        validators=[
            FileRequired(message="Please upload a spec sheet."),
            FileAllowed({"pdf", "docx", "xlsx"}, "Allowed file types: PDF, DOCX, XLSX.")
        ]
    )
    submit = SubmitField("Upload")

# Upload Test Plan Form
class UploadTestPlanForm(FlaskForm):
    test_plan_file = FileField(
        "Test Plan File",
        validators=[
            FileRequired(message="Please upload a test plan."),
            FileAllowed({"pdf", "csv", "txt"}, "Allowed file types: PDF, CSV, TXT.")
        ]
    )
    submit = SubmitField("Upload")

# Add Valve Form
class AddValveForm(FlaskForm):
    name = StringField(
        "Valve Name",
        validators=[
            DataRequired(),
            Length(max=255, message="Name must not exceed 255 characters.")
        ]
    )
    valve_type = StringField(
        "Valve Type",
        validators=[
            DataRequired(),
            Length(max=255, message="Type must not exceed 255 characters.")
        ]
    )
    api_endpoint = StringField(
        "API Endpoint",
        validators=[Optional(), Regexp(r'^https?://', message="Must be a valid URL.")]
    )
    specifications = TextAreaField("Specifications", validators=[Optional()])
    submit = SubmitField("Add Valve")

# Run Test Plan Form
class RunTestPlanForm(FlaskForm):
    test_plan_id = IntegerField(
        "Test Plan ID",
        validators=[DataRequired(), Regexp(r'^\d+$', message="Must be a valid ID.")]
    )
    submit = SubmitField("Run Test Plan")

# General Settings Form
class SettingsForm(FlaskForm):
    key = StringField("Setting Key", validators=[DataRequired()])
    value = StringField("Setting Value", validators=[DataRequired()])
    submit = SubmitField("Save Setting")
    
