HardwareTester/
│
├── HardwareTester/                 # Core application package
│   ├── __init__.py                 # Flask app factory, initializes app and extensions
│   ├── views.py                    # Flask routes and API endpoints
│   ├── models.py                   # SQLAlchemy database models
│   ├── sockets.py                  # SocketIO setup and real-time log handling
│   ├── templates/                  # HTML templates for the frontend
│   │   ├── base.html               # Base template with common layout
│   │   ├── dashboard.html          # Main dashboard for user interaction
│   │   ├── upload_test_plan.html   # Optional separate page for uploading test plans
│   │   ├── valve_management.html   # Optional separate page for managing valves
│   ├── static/                     # Static assets (CSS, JS, images)
│   │   ├── css/
│   │   │   ├── styles.css          # Custom styles for the app
│   │   ├── js/
│   │   │   ├── app.js              # JavaScript for dynamic frontend functionality
│   │   ├── img/
│   │       ├── logo.png            # Example logo for the app
│   ├── utils/                      # Utilities and helper functions
│   │   ├── __init__.py             # Exposes all utilities as a module
│   │   ├── parsers.py              # Functions for parsing test plans and spec sheets
│   │   ├── test_runner.py          # Functions for running and simulating test plans
│   │   ├── hardware_manager.py     # Functions for managing hardware (valves, etc.)
│   │   ├── auto_deploy.py          # Functions for build and deploy processes
│   │   ├── validators.py           # Input validation utilities
│   ├── config.py                   # Central configuration for Flask and app settings
│   ├── forms.py                    # Flask-WTF forms for file uploads and other inputs
│   ├── extensions.py               # Initialize extensions like SQLAlchemy, SocketIO
│
├── migrations/                     # Database migration files (Flask-Migrate)
│
├── tests/                          # Unit and integration tests
│   ├── __init__.py
│   ├── test_views.py               # Tests for Flask routes
│   ├── test_utils.py               # Tests for utility functions
│   ├── test_models.py              # Tests for database models
│   ├── test_sockets.py             # Tests for real-time SocketIO functionality
│
├── uploads/                        # Directory for uploaded files
│   ├── spec_sheets/                # Uploaded spec sheets
│   ├── test_plans/                 # Uploaded test plans
│
├── .env                            # Environment variables for configuration
├── .flaskenv                       # Flask environment configuration
├── .gitignore                      # Git ignore file to exclude unnecessary files
├── requirements.txt                # Python dependencies
├── runserver.py                    # Entry point to start the Flask app
├── README.md                       # Project documentation
