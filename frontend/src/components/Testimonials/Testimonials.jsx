import React from 'react';
import './Testimonials.css';

const Testimonials = () => {
  return (
    <section className="testimonials-section">
      <div className="testimonials-container">
        
        <div className="main-testimonial">
          <div className="quote-mark large">&ldquo;</div>
          <blockquote className="main-quote">
            The cardamom from Balaji is unlike anything we have sourced before. The aroma is extraordinary, and the consistency batch after batch gives us the confidence to use it across our entire product line.
          </blockquote>
          <div className="main-author">
            <strong>Rajesh Kumar</strong>
            <span>Head Chef, Taj Hotels Bengaluru</span>
          </div>
        </div>

        <div className="testimonials-grid">
          <div className="testimonial-card">
            <div className="quote-mark small">&ldquo;</div>
            <p className="card-quote">
              We switched to Balaji's chilli powder two years ago. The colour, heat profile, and shelf stability are consistently superior.
            </p>
            <div className="card-author">
              <strong>Meera Patel</strong>
              <span>Procurement Lead, MTR Foods</span>
            </div>
          </div>
          
          <div className="testimonial-card">
            <div className="quote-mark small">&ldquo;</div>
            <p className="card-quote">
              Reliable, honest, and the ragi flour is genuinely stone-ground. You can taste the difference.
            </p>
            <div className="card-author">
              <strong>Sundar Krishnamurthy</strong>
              <span>Founder, Organic Basket</span>
            </div>
          </div>
          
          <div className="testimonial-card">
            <div className="quote-mark small">&ldquo;</div>
            <p className="card-quote">
              Their commitment to quality and consistency makes them an ideal partner for our bulk spice requirements across multiple facilities.
            </p>
            <div className="card-author">
              <strong>Amit Singh</strong>
              <span>Operations Director, FoodWorks</span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Testimonials;
