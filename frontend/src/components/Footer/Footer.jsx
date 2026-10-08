import React from 'react';
import { Globe, MessageCircle, Camera, Briefcase } from 'lucide-react';
import './Footer.css';

const Footer = () => {
  return (
    <footer className="footer">
      <div className="footer-container">
        <div className="footer-top">
          <div className="footer-col brand-col">
            <h2 className="footer-logo">Balaji Ingredients</h2>
            <p className="footer-company-type">PRIVATE LIMITED</p>
            <p className="footer-tagline">
              Delivering premium quality spices and flours to businesses worldwide, preserving authentic flavors since inception.
            </p>
            <div className="social-links">
              <a href="#" aria-label="Facebook"><Globe size={20} /></a>
              <a href="#" aria-label="Twitter"><MessageCircle size={20} /></a>
              <a href="#" aria-label="Instagram"><Camera size={20} /></a>
              <a href="#" aria-label="LinkedIn"><Briefcase size={20} /></a>
            </div>
          </div>
          
          <div className="footer-col">
            <h3 className="footer-col-title">Products</h3>
            <ul className="footer-links">
              <li><a href="#chilli">Red Chilli Powder</a></li>
              <li><a href="#pepper">Malabar Black Pepper</a></li>
              <li><a href="#cardamom">Green Cardamom</a></li>
              <li><a href="#ragi">Ragi Flour</a></li>
            </ul>
          </div>
          
          <div className="footer-col">
            <h3 className="footer-col-title">Company</h3>
            <ul className="footer-links">
              <li><a href="#story">Our Story</a></li>
              <li><a href="#certifications">Certifications</a></li>
              <li><a href="#partners">B2B Partners</a></li>
              <li><a href="#careers">Careers</a></li>
            </ul>
          </div>
          
          <div className="footer-col contact-col">
            <h3 className="footer-col-title">Contact Us</h3>
            <div className="footer-contact-info">
              <p>+91 63606 35801</p>
              <p>+91 79962 60020</p>
              <p>info@balajiingredients.in</p>
              <p>Peenya Industrial Area,<br />Bengaluru, Karnataka 560058</p>
            </div>
          </div>
        </div>
        
        <div className="footer-bottom">
          <p className="copyright">© 2024 Balaji Ingredients Pvt. Ltd. All rights reserved.</p>
          <p className="director">Director: Chandan Y Gowdaa</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
