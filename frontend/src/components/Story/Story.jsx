import React from 'react';
import './Story.css';
import { Sprout, FlaskConical, Cog, Package } from 'lucide-react';

const Story = () => {
  return (
    <section className="story-section">
      <div className="story-container">
        <div className="story-left">
          <div className="story-image-wrapper">
            <img src="/images/market_spices.jpg" alt="Spice Market" className="story-main-image" />
            <div className="story-card-overlay bottom-left">
              <span className="story-location-tag">KARNATAKA &middot; INDIA</span>
              <p className="story-overlay-quote">Where the aroma begins.</p>
            </div>
            <div className="story-card-overlay bottom-right">
              <span className="story-since-tag">SINCE 2015</span>
              <p className="story-overlay-text">A decade of trusted supply.</p>
              <div className="story-overlay-stats">
                <div className="story-overlay-stat">
                  <span className="stat-num">10+</span>
                  <span className="stat-label">YEARS OF SOURCING</span>
                </div>
                <div className="story-overlay-stat">
                  <span className="stat-num">4</span>
                  <span className="stat-label">SIGNATURE PRODUCTS</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div className="story-right">
          <span className="section-label">OUR STORY</span>
          <h2 className="story-heading">
            A quiet obsession with <span className="story-italic-red">honest spice.</span>
          </h2>
          <p className="story-paragraph">
            Balaji Ingredients began in a small warehouse in Bengaluru with one rule: never pack anything we would not cook with at home. Ten years later, that rule still runs the company.
          </p>
          
          <div className="story-features-grid">
            <div className="feature-card">
              <Sprout className="feature-icon" />
              <div className="feature-content">
                <h3 className="feature-title">Direct from Farm</h3>
                <p className="feature-desc">Grower relationships in Byadgi, Idukki, and rural Karnataka.</p>
              </div>
            </div>
            <div className="feature-card">
              <FlaskConical className="feature-icon" />
              <div className="feature-content">
                <h3 className="feature-title">Batch-Tested</h3>
                <p className="feature-desc">NABL-accredited labs verify piperine, ASTA, moisture and pesticides.</p>
              </div>
            </div>
            <div className="feature-card">
              <Cog className="feature-icon" />
              <div className="feature-content">
                <h3 className="feature-title">Slow-Milled</h3>
                <p className="feature-desc">Stone and hammer-milling at low temperatures to protect volatile oils.</p>
              </div>
            </div>
            <div className="feature-card">
              <Package className="feature-icon" />
              <div className="feature-content">
                <h3 className="feature-title">B2B Ready</h3>
                <p className="feature-desc">Bulk sacks, private-label packing and IndiaMART pan-India dispatch.</p>
              </div>
            </div>
          </div>
          
          <div className="story-certifications">
            <span className="cert-pill">FSSAI Licensed</span>
            <span className="cert-pill">ISO 22000 Certified</span>
            <span className="cert-pill">APEDA Registered</span>
            <span className="cert-pill">Spices Board India</span>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Story;
