import React from 'react';
import { ArrowUpRight } from 'lucide-react';
import './Products.css';
import products from '../../data/products.js';

const Products = () => {
  return (
    <section className="products-section">
      <div className="products-header">
        <div className="products-header-left">
          <span className="products-label">CATALOGUE · 04</span>
          <h2 className="products-title">The Signature Four</h2>
        </div>
        <div className="products-header-right">
          <p className="products-subtitle">
            A tight, uncompromising catalogue — each item earning its place.
          </p>
        </div>
      </div>
      
      <div className="products-grid">
        {products.map((product, index) => {
          const isOverlaid = index === 0 || index === 1;
          const cardClass = isOverlaid ? 'product-card overlaid' : 'product-card standard';
          
          return (
            <div key={index} className={cardClass}>
              <div className="product-image-container">
                <img src={product.image} alt={product.name} className="product-image" />
                <div className="product-badge">{product.category}</div>
                <div className="product-arrow">
                  <ArrowUpRight size={24} />
                </div>
                {isOverlaid && <div className={`product-gradient product-gradient-${index}`}></div>}
              </div>
              
              <div className="product-content">
                <div className="product-info">
                  <h3 className="product-name">{product.name}</h3>
                  <p className="product-desc">{product.description}</p>
                </div>
                <div className="product-price">
                  <span>FROM ₹{product.price} / kg</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
};

export default Products;
