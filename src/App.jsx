import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation, Navigate } from 'react-router-dom';
import { ProjectProvider } from './context/ProjectContext';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';

import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import WizardPage from './pages/WizardPage';
import ProjectPage from './pages/ProjectPage';
import GeneratingPage from './pages/GeneratingPage';
import FloorplansPage from './pages/FloorplansPage';
import GalleryPage from './pages/GalleryPage';

function AppLayout() {
  const location = useLocation();
  const isGeneratingView = location.pathname.includes('/generating');

  return (
    <div className="flex flex-col" style={{ minHeight: '100vh' }}>
      <Navbar />

      <div className="flex-1">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/projects" element={<DashboardPage />} />
          <Route path="/projects/new" element={<WizardPage />} />
          <Route path="/projects/:id" element={<ProjectPage />} />
          <Route path="/projects/:id/generating" element={<GeneratingPage />} />
          <Route path="/projects/:id/floorplans" element={<FloorplansPage defaultStudioTab="cad" />} />
          <Route path="/projects/:id/design" element={<FloorplansPage defaultStudioTab="3d" />} />
          <Route path="/projects/:id/cad" element={<FloorplansPage defaultStudioTab="cad" />} />
          <Route path="/projects/:id/gallery" element={<GalleryPage />} />
          {/* Fallback to landing */}
          <Route path="*" element={<LandingPage />} />
        </Routes>
      </div>

      {!isGeneratingView && <Footer />}
    </div>
  );
}

export default function App() {
  return (
    <ProjectProvider>
      <Router>
        <AppLayout />
      </Router>
    </ProjectProvider>
  );
}
