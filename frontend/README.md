# Emulator Dashboard

This project is an emulator dashboard built with TypeScript and React. It provides a user interface to manage and interact with an emulator.

## Project Structure

```
emulator-dashboard
├── src
│   ├── main.ts          # Entry point of the application
│   ├── components
│   │   └── Dashboard.tsx # Main dashboard component
│   ├── services
│   │   └── EmulatorService.ts # Service for emulator interactions
│   └── types
│       └── index.ts     # Type definitions used in the application
├── package.json         # NPM configuration file
├── tsconfig.json        # TypeScript configuration file
└── README.md            # Project documentation


Revised layout - Revision 8zillion and freaking 7

frontend/
├── public/
│   ├── index.html
│   ├── favicon.ico
│   ├── manifest.json
│   ├── robots.txt
│   ├── logo192.png
│   ├── logo512.png
│   └── styles.css

├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── index.css // 🆕 Global styles (tailwind or plain)
│   ├── assets/
│   ├── context/
│   │   ├── DeviceContext.tsx // 🆕 holds current hardware/emulator
│   │   └── UserContext.tsx // 🆕 login/auth state
│   ├── hooks/
│   │   ├── useFetch.ts // 🆕 generic fetcher
│   │   ├── useMQTT.ts // 🆕 mqtt management hook
│   │   └── useMirrorMode.ts // 🆕 manages device mirroring
│   ├── routes/
│   │   └── index.tsx // 🆕 react-router dom setup
│   ├── types/
│   │   └── index.ts
│   ├── services/
│   │   ├── authService.ts
│   │   ├── dashboardService.ts
│   │   ├── emulatorService.ts
│   │   ├── hardwareService.ts
│   │   ├── mqttService.ts
│   │   ├── notificationService.ts
│   │   ├── serialService.ts
│   │   └── userManagementService.ts // 🆕 rename for consistency

│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Sidebar.tsx // 🆕
│   │   │   ├── Topbar.tsx // 🆕
│   │   │   └── DashboardLayout.tsx // 🆕 wrapper for all dashboards
│   │   ├── common/
│   │   │   ├── MirrorModal.tsx
│   │   │   ├── SerialPanel.tsx
│   │   │   ├── ToggleSwitch.tsx // 🆕 reuse for mirroring, toggles
│   │   │   └── ConfirmDialog.tsx // 🆕
│   │   ├── EmulatorDashboard/
│   │   │   ├── EmulatorPanel.tsx
│   │   │   └── ActiveEmulations.tsx
│   │   ├── ConnectionDashboard/
│   │   │   └── MQTTPanel.tsx
│   │   ├── FirmwareDashboard/
│   │   │   ├── FirmwareUploader.tsx // 🆕
│   │   │   ├── FirmwareValidator.tsx // 🆕
│   │   │   └── FirmwareTable.tsx // 🆕
│   │   ├── HardwareDashboard/
│   │   │   └── HardwarePanel.tsx
│   │   ├── Metrics/
│   │   │   ├── HardwareLogsMetrics.tsx
│   │   │   ├── LiveMetrics.tsx
│   │   │   └── SystemHealthPanel.tsx
│   │   ├── PeripheralManager/
│   │   │   ├── PeripheralList.tsx // 🆕
│   │   │   ├── PeripheralEditor.tsx // 🆕
│   │   │   └── PeripheralMapper.tsx // 🆕
│   │   ├── TestDashboard/
│   │   │   ├── CodeScanner.tsx
│   │   │   ├── TestPlanManager.tsx
│   │   │   └── TestResultsPanel.tsx
│   │   ├── UserDashboard/
│   │   │   ├── Dashboard.tsx
│   │   │   └── UserManagementPanel.tsx
│   │   └── SettingsPanel/
│   │       └── GlobalSettings.tsx // 🆕 hostname, ports, paths, etc.

└── tsconfig.json




```

## Getting Started

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/emulator-dashboard.git
   ```

2. Navigate to the project directory:
   ```
   cd emulator-dashboard
   ```

3. Install the dependencies:
   ```
   npm install
   ```

4. Start the application:
   ```
   npm start
   ```

## Features

- Start and stop the emulator
- View the current status of the emulator
- User-friendly interface for managing emulator settings

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for details.