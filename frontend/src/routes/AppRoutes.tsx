// src/routes/AppRoutes.tsx
import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";

import DashboardLayout from "@/components/Layout/DashboardLayout";

import EmulatorDashboard from "@/components/EmulatorDashboard/EmulatorDashboard";
import ConnectionDashboard from "@/components/ConnectionDashboard/ConnectionDashboard"

import TestPlanManager from "@/components/Tests/TestPlanManager";
import UserManagementPanel from "@/components/User/UserManagementPanel";
import HardwareDashboard from "@/components/HardwareDashboard/HardwareDashboard";

import FirmwareDashboard from "@/components/FirmwareDashboard/FirmwareDashboard";
import MetricsDashboard from "@/components/Metrics/MetricsDashboard";

import PeripheralDashboard from "@/components/PeripheralManager/PeripheralDashboard";
import Settings from "@/components/Settings/SettingsPanel";
import UserDashboard from "../components/User/UserDashboard";

const AppRoutes: React.FC = () => {
    return (
        <DashboardLayout>
            <Routes>
                {/* Default - Emulator */}
                <Route path="/" element={<Navigate to="/emulator" replace />} />

                {/* Emulator */}
                <Route path="/emulator" element={<EmulatorDashboard />} />

                {/* Connections */}
                <Route path="/connect" element={<ConnectionDashboard />} />
                
                {/* Tests */}
                <Route path="/tests" element={<TestPlanManager />} />

                {/* User Management */}
                <Route path="/user-management" element={<UserManagementPanel />} />

                {/* User */}
                <Route path="/user" element={<UserDashboard />} />

                {/* Hardware */}
                <Route path="/hardware" element={<HardwareDashboard />} />

                {/* Firmware */}
                <Route path="/firmware" element={<FirmwareDashboard />} />

                {/* Metrics */}
                <Route path="/metrics" element={<MetricsDashboard />} />

                {/* Peripherals */}
                <Route path="/peripherals" element={<PeripheralDashboard />} />

                {/* Settings */}
                <Route path="/settings" element={<Settings />} />

                {/* 404 */}
                <Route path="*" element={<h2>404 - Page Not Found</h2>} />
            </Routes>
        </DashboardLayout>
    );
};

export default AppRoutes;
