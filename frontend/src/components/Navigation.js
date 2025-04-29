import React from 'react';
import { Link } from 'react-router-dom';

const Navigation = () => {
  return (
    <nav className="navigation">
      <div className="nav-brand">
        <Link to="/" className="nav-logo">Pub-it</Link>
      </div>
      <div className="nav-links">
        <Link to="/members" className="nav-link">Members</Link>
        <Link to="/publications" className="nav-link">Publications</Link>
      </div>
    </nav>
  );
};

export default Navigation; 