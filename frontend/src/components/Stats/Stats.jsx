import React from 'react';
import './Stats.css';

const Stats = () => {
  const statData = [
    { number: '10+', label: 'YEARS OF SOURCING' },
    { number: '4', label: 'SIGNATURE PRODUCTS' },
    { number: '120+', label: 'B2B PARTNERS' },
    { number: '99.4%', label: 'PURITY ASSURED' },
  ];

  return (
    <section className="stats-section">
      <div className="stats-container">
        {statData.map((stat, index) => (
          <div className="stat-item" key={index}>
            <h3 className="stat-number">{stat.number}</h3>
            <p className="stat-text">{stat.label}</p>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Stats;
