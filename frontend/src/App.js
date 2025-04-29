import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Navigation from './components/Navigation';
import LandingPage from './components/LandingPage';
import PublicationsList from './components/PublicationsList';
import MembersList from './components/MembersList';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <Navigation />
        <main className="main-content">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/members" element={<MembersList />} />
            <Route path="/publications" element={<PublicationsList />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App; 