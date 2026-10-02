import React from 'react';
import { Link, useLocation } from 'react-router-dom';

export default function Navbar() {
  const location = useLocation();
  const currentPath = location.pathname;

  const isActive = (path) => currentPath === path || (path !== '/' && currentPath.startsWith(path));

  return (
    <header className="navbar" role="banner">
      <div className="navbar__inner">
        <Link to="/" className="navbar__logo" aria-label="ZYNORA AI Home">
          <div className="navbar__logo-symbol">Z</div>
          <span>ZYNORA</span>
          <span className="navbar__logo-accent">AI</span>
        </Link>

        <nav className="navbar__nav" aria-label="Primary Navigation">
          <Link
            to="/"
            className={`navbar__link ${currentPath === '/' ? 'active' : ''}`}
          >
            Overview
          </Link>
          <Link
            to="/projects/new"
            className={`navbar__link ${isActive('/projects/new') ? 'active' : ''}`}
          >
            Create Project
          </Link>
          <Link
            to="/projects"
            className={`navbar__link ${currentPath === '/projects' ? 'active' : ''}`}
          >
            Dashboard
          </Link>
        </nav>

        <div className="navbar__actions">
          <Link to="/projects/new" className="btn btn-primary btn-sm">
            Create Floor Plan
          </Link>
        </div>
      </div>
    </header>
  );
}
