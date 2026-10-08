import React from 'react';
import { ArrowRight, Plus } from 'lucide-react';
// import { products } from '../../data/products.js'; // Will be used when data exists
import './Hero.css';

const Hero = () => {
  return (
    <section className="hero-section">
      <div className="hero-container">
        
        {/* Left Content */}
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-icon">✦</span>
            <span>ESTATE · STONE-MILLED · SINCE 2015</span>
          </div>
          
          <h1 className="hero-title">
            The spice of <br />
            <span className="hero-title-italic">South India,</span> <br />
            bottled with care.
          </h1>
          
          <p className="hero-description">
            Balaji Ingredients hand-picks red chilli, black pepper, cardamom and ragi at their peak — then mills them slowly, so the aroma never leaves the bag.
          </p>
          
          <div className="hero-actions">
            <button className="btn-explore">
              Explore Catalogue <ArrowRight size={18} />
            </button>
            <button className="btn-wholesale">
              Request Wholesale Pricing
            </button>
          </div>
          
          <div className="hero-trust">
            <span>✦ 100% Natural</span>
            <span>✦ FSSAI · ISO 22000</span>
            <span>✦ Lab-Tested Batches</span>
          </div>
        </div>

        {/* Right: Product Cards Grid */}
        <div className="hero-cards-grid">
          {/* Card 1: Chilli (Largest, bottom left) */}
          <div className="hero-card card-chilli">
            <div className="card-badge">SIGNATURE</div>
            <div className="card-image-placeholder">
               <img src="/images/chilli_product.jpg" alt="Guntur Sannam Chilli" />
            </div>
            <div className="card-info">
              <h3>Guntur Sannam Chilli Powder</h3>
              <button className="btn-plus"><Plus size={16} /></button>
            </div>
          </div>
          
          {/* Card 2: Pepper (Smaller, top right) */}
          <div className="hero-card card-pepper">
            <div className="card-badge">SIGNATURE</div>
            <div className="card-image-placeholder">
               <img src="/images/pepper_product.jpg" alt="Malabar Black Pepper" />
            </div>
            <div className="card-info">
              <span className="card-meta">WHOLE & COARSE GROUND</span>
              <h3>Malabar Black Pepper</h3>
              <button className="btn-plus"><Plus size={16} /></button>
            </div>
          </div>

          {/* Card 3: Cardamom (Mid left) */}
          <div className="hero-card card-cardamom">
            <div className="card-badge">SIGNATURE</div>
            <div className="card-image-placeholder">
              <img src="/images/cardamom_product.jpg" alt="Green Cardamom" />
            </div>
            <div className="card-info">
              <h3>Green Cardamom</h3>
              <button className="btn-plus"><Plus size={16} /></button>
            </div>
          </div>

          {/* Card 4: Ragi (Lower right) */}
          <div className="hero-card card-ragi">
            <div className="card-image-placeholder">
               <img src="/images/ragi_product.jpg" alt="Ragi Flour" />
            </div>
            <div className="card-info">
              <span className="card-meta">FINGER MILLET · SPROUTED OPTION</span>
              <h3>Stone-Ground Ragi Flour</h3>
              <button className="btn-plus"><Plus size={16} /></button>
            </div>
          </div>
        </div>

      </div>
    </section>
  );
};

export default Hero;
