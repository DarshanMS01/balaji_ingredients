import React, { useState, useEffect } from 'react';
import { Phone, ChevronRight, User } from 'lucide-react';
import './Navbar.css';

const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <header className={`navbar-header ${scrolled ? 'scrolled' : ''}`}>
      <div className="navbar-container">
        {/* Left: Logo Area */}
        <div className="navbar-logo-area">
          <div className="navbar-logo-icon">
            B
          </div>
          <div className="navbar-logo-text">
            <span className="navbar-logo-title">Balaji Ingredients</span>
            <span className="navbar-logo-subtitle">PRIVATE LIMITED</span>
          </div>
        </div>

        {/* Center: Nav links */}
        <nav className="navbar-links">
          <a href="#home" className="nav-link active">Home</a>
          <a href="#products" className="nav-link">Products</a>
          <a href="#story" className="nav-link">Our Story</a>
          <a href="#contact" className="nav-link">Contact</a>
        </nav>

        {/* Right: Phone & CTA */}
        <div className="navbar-actions">
          <a href="tel:+916360635801" className="navbar-phone">
            <Phone size={18} />
            <span>+91 63606 35801</span>
          </a>
          <a href="#/login" className="navbar-login">
            <User size={18} />
            <span>Login</span>
          </a>
          <button className="navbar-cta">
            Request a Quote
          </button>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
