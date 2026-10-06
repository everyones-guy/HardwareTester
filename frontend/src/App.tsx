// src/App.tsx
import React, { Suspense } from "react";
import { Route, Routes } from 'react-router-dom';
import Workbench from './workbench/Workbench';
const LegacyApp = React.lazy(() => import('./LegacyApp'));
const App: React.FC = () => <Routes>
    <Route path="/legacy/*" element={<Suspense fallback={<p>Loading original dashboards…</p>}><LegacyApp /></Suspense>} />
    <Route path="/*" element={<Workbench />} />
</Routes>;

export default App;
