import React from 'react';
import './App.css';
import Navbar from './components/Navbar/Navbar';
import Hero from './components/Hero/Hero';
import Marquee from './components/Marquee/Marquee';
import Products from './components/Products/Products';
import Story from './components/Story/Story';
import Stats from './components/Stats/Stats';
import Testimonials from './components/Testimonials/Testimonials';
import Contact from './components/Contact/Contact';
import Footer from './components/Footer/Footer';
import Login from './components/Login/Login';

function App() {
  const [currentHash, setCurrentHash] = React.useState(window.location.hash);

  React.useEffect(() => {
    const handleHashChange = () => setCurrentHash(window.location.hash);
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  if (currentHash === '#/login') {
    return (
      <div className="app">
        <Login />
      </div>
    );
  }

  return (
    <div className="app">
      <Navbar />
      <Hero />
      <Marquee />
      <Products />
      <Story />
      <Stats />
      <Testimonials />
      <Contact />
      <Footer />
    </div>
  );
}

export default App;
