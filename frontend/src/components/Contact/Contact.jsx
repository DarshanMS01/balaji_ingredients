import React from 'react';
import { Phone, Mail, MapPin } from 'lucide-react';
import './Contact.css';

const Contact = () => {
  return (
    <section className="contact-section" id="contact">
      <div className="contact-container">
        <div className="contact-header">
          <span className="contact-label">GET IN TOUCH</span>
          <h2 className="contact-heading">Request a Quote</h2>
        </div>
        
        <div className="contact-content">
          <div className="contact-info">
            <p className="contact-intro">
              Looking for premium spices and flours for your business? Reach out to us for bulk orders, customized packaging, and business partnerships.
            </p>
            
            <div className="info-list">
              <div className="info-item">
                <div className="icon-circle">
                  <Phone size={24} />
                </div>
                <div className="info-text">
                  <h3>Phone</h3>
                  <p>+91 63606 35801</p>
                  <p>+91 79962 60020</p>
                </div>
              </div>
              
              <div className="info-item">
                <div className="icon-circle">
                  <Mail size={24} />
                </div>
                <div className="info-text">
                  <h3>Email</h3>
                  <p>info@balajiingredients.in</p>
                </div>
              </div>
              
              <div className="info-item">
                <div className="icon-circle">
                  <MapPin size={24} />
                </div>
                <div className="info-text">
                  <h3>Address</h3>
                  <p>Peenya Industrial Area, Bengaluru, Karnataka 560058</p>
                </div>
              </div>
            </div>
          </div>
          
          <div className="contact-form-wrapper">
            <form className="contact-form" onSubmit={(e) => e.preventDefault()}>
              <div className="form-group-row">
                <div className="form-group">
                  <label htmlFor="fullName">Full Name</label>
                  <input type="text" id="fullName" placeholder="Your Name" required />
                </div>
                <div className="form-group">
                  <label htmlFor="companyName">Company Name</label>
                  <input type="text" id="companyName" placeholder="Your Company" />
                </div>
              </div>
              
              <div className="form-group-row">
                <div className="form-group">
                  <label htmlFor="email">Email</label>
                  <input type="email" id="email" placeholder="your@email.com" required />
                </div>
                <div className="form-group">
                  <label htmlFor="phone">Phone Number</label>
                  <input type="tel" id="phone" placeholder="+91 00000 00000" required />
                </div>
              </div>
              
              <div className="form-group">
                <label htmlFor="product">Product Interest</label>
                <select id="product" required defaultValue="">
                  <option value="" disabled>Select a Product</option>
                  <option value="chilli">Red Chilli Powder</option>
                  <option value="pepper">Malabar Black Pepper</option>
                  <option value="cardamom">Green Cardamom</option>
                  <option value="ragi">Ragi Flour</option>
                  <option value="other">Other</option>
                </select>
              </div>
              
              <div className="form-group">
                <label htmlFor="message">Quantity / Message</label>
                <textarea id="message" rows="4" placeholder="Tell us about your requirements..." required></textarea>
              </div>
              
              <button type="submit" className="submit-btn">Send Enquiry</button>
            </form>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Contact;
