# Hardware Tester

Hardware Tester is a Flask-based application for testing and managing hardware devices such as valves, peripherals, and MQTT-connected devices. The app provides a robust interface for hardware interaction, configuration, and real-time monitoring.

## Features

- **Valve Management**
  - Add, remove, and view valves in the system.
  - Upload and manage valve specification sheets.
  - Save and load valve configurations.

- **Test Plan Management**
  - Upload and execute test plans.
  - View test results and logs.
  - Configure test plans dynamically.

- **Real-Time Logs**
  - View real-time logs using WebSocket updates.
  - Search and filter logs for better debugging.

- **Configuration Management**
  - Save configurations for valves and peripherals.
  - Load previously saved configurations.
  - Visualize configurations with an interactive canvas.

- **MQTT Management**
  - Connect to MQTT brokers.
  - Publish and subscribe to topics.
  - Discover devices over MQTT.

- **Serial Communication**
  - Communicate with hardware via serial (USB-to-serial) connections.
  - Send and receive data.
  - Parse JSON responses from connected devices.

- **Hardware Visualization**
  - Interactive, drag-and-drop canvas to visualize hardware configurations.
  - Animated components showing real-time states (e.g., open/closed valves).
  - Clickable UI elements to simulate and control hardware functions.

- **User Management**
  - User authentication and registration.
  - Profile management.

---

## Setup Instructions

### Prerequisites

- Python 3.8 or later
- A virtual environment tool (recommended)
- Node.js and npm (for managing front-end dependencies)

### Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/everyones-guy/HardwareTester.git
   cd hardware-tester
   ```

2. **Set Up a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**
   Create a `.env` file in the root directory with the following:
   ```env
   FLASK_ENV=development
   SECRET_KEY=your-secret-key
   DATABASE_URL=sqlite:///app.db
   BASE_URL=http://127.0.0.1:5000
   MQTT_BROKER=test.mosquitto.org
   MQTT_PORT=1883
   MQTT_USERNAME=your-username
   MQTT_PASSWORD=your-password
   DEFAULT_SERIAL_PORT=COM3
   DEFAULT_BAUDRATE=9600
   ```

5. **Initialize the Database**
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. **Run the Application**
   ```bash
   flask run
   ```

7. **Access the Application**
   Open your browser and navigate to `http://127.0.0.1:5000`.

---

## Usage Instructions

### Valve Management

1. Navigate to the **Valve Management** page.
2. Add new valves by providing the name, type, and optional API endpoint.
3. Upload specification sheets in supported formats (PDF, DOCX, XLSX).
4. View valve statuses and configurations in real-time.

### Test Plan Management

1. Navigate to the **Test Plan Management** page.
2. Upload test plans in supported formats (PDF, CSV, TXT).
3. Run test plans and view detailed results.
4. Save and load test plans for reuse.

### Real-Time Logs

1. Navigate to the **Real-Time Logs** page.
2. View live logs streamed from the server.
3. Use search and filter options for easier debugging.

### Configuration Management

1. Navigate to the **Configuration Management** page.
2. Use the interactive canvas to visualize and manage configurations.
3. Drag and drop components to set up hardware layouts.
4. Save configurations for future use.

### MQTT Management

1. Navigate to the **MQTT Management** page.
2. Connect to an MQTT broker using the provided credentials.
3. Publish messages to topics or subscribe to receive data.
4. Discover connected devices over MQTT.

### Serial Communication

1. Navigate to the **Hardware Devices** page.
2. Connect to devices using the configured serial port and baud rate.
3. Send and receive data in real-time.
4. Parse JSON responses or view raw data.

---

## Configuration

- All settings are managed through the `.env` file. Update the variables as needed for your environment.
- Custom configurations can also be added by modifying `config.py`.

---

## Development

### Testing

Run unit tests with:
```bash
pytest
```

### Linting

Ensure code quality with:
```bash
flake8
```

### Static Files

If you need to rebuild static assets:
```bash
npm install
npm run build
```

---

## Deployment

1. Set the `FLASK_ENV` to `production` in your `.env` file.
2. Use a production WSGI server like Gunicorn:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 runserver:app
   ```

---

## Contributing

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Description of changes"
   ```
4. Push to your fork and create a pull request.

---

## Support

If you encounter issues or have feature requests, please open an issue in the repository.

---

## License

This project is licensed under the MIT License.
```

This format ensures clarity, proper markdown structure, and detailed instructions for using the application.
