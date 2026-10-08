import React from 'react';
import './Marquee.css';

const items = [
  'Idukki Cardamom',
  'Karnataka Ragi',
  'Batch Tested',
  'Byadgi Chilli',
  'Malabar Pepper',
  'Stone-Milled',
  'FSSAI Licensed',
  'ISO 22000'
];

const Marquee = () => {
  return (
    <div className="marquee-container">
      <div className="marquee-content">
        {[...items, ...items, ...items].map((item, index) => (
          <React.Fragment key={index}>
            <span className="marquee-item">{item}</span>
            <span className="marquee-separator">✦</span>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default Marquee;
