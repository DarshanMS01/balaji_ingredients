import React, { useState } from 'react';
import { Eye, EyeOff, Lock, Mail, ArrowRight, ShieldCheck } from 'lucide-react';
import './Login.css';

const Login = () => {
  const [identifier, setIdentifier] = useState('trade@balajiingredients.com');
  const [password, setPassword] = useState('Balaji@2026!');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!identifier || !password) {
      setMessage({ type: 'error', text: 'Please fill in all required fields.' });
      return;
    }

    setLoading(true);
    setMessage(null);

    // Call Django API or sync state
    setTimeout(() => {
      try {
        localStorage.setItem('balaji_logged_in', 'true');
        localStorage.setItem('balaji_user', JSON.stringify({
          name: identifier.split('@')[0].toUpperCase(),
          email: identifier,
          role: 'Wholesale Partner'
        }));
      } catch (err) {
        console.warn('Storage error:', err);
      }
      setLoading(false);
      setMessage({ type: 'success', text: 'Sign in successful! Redirecting...' });
      setTimeout(() => {
        window.location.hash = '';
      }, 700);
    }, 600);
  };

  const handleQuickFill = () => {
    setIdentifier('trade@balajiingredients.com');
    setPassword('Balaji@2026!');
  };

  return (
    <div className="react-login-container">
      {/* Left Brand Side */}
      <section className="story-side">
        <header className="story-header">
          <a href="#" onClick={(e) => { e.preventDefault(); window.location.hash = ''; }} className="brand-logo-wrap">
            <div className="flame-badge">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2c-.8 2.5-3 4.8-3 7.5 0 3 2.2 5.5 5 5.5s5-2.5 5-5.5c0-1.2-.5-2.3-1.2-3.2-.2 1.5-1.3 2.7-2.8 2.7-1.7 0-3-1.3-3-3 0-1.5.8-2.8 2-3.5-.7-.3-1.4-.5-2-.5z"/>
              </svg>
            </div>
            <div>
              <div className="brand-name">Balaji</div>
              <div className="brand-sub">Ingredients</div>
            </div>
          </a>
          <button type="button" className="btn-back" onClick={() => { window.location.hash = ''; }}>
            Back to Website
          </button>
        </header>

        <div className="story-content">
          <div className="kicker">● B2B Ingredients Portal</div>
          <h1 className="headline">
            The Authentic Aroma of<br />
            <em>Pure Indian Spices.</em>
          </h1>
          <p className="desc">
            Hand-picking red chilli, black pepper, cardamom, and ragi at their peak — milled slowly for global food processors and commercial enterprises.
          </p>

          <div className="pillars-grid">
            <div className="pillar-card">
              <div>
                <h3>Peak Harvest</h3>
                <p>Direct grower sourcing</p>
              </div>
            </div>
            <div className="pillar-card">
              <div>
                <h3>Slow-Milled</h3>
                <p>Zero additives</p>
              </div>
            </div>
            <div className="pillar-card">
              <div>
                <h3>Bulk Freight</h3>
                <p>Pan-India supply</p>
              </div>
            </div>
          </div>
        </div>

        <footer className="story-footer">
          <span>ESTD. 1982 · CHITRADURGA & BENGALURU, KARNATAKA</span>
          <span>FSSAI & EXPORT CERTIFIED</span>
        </footer>
      </section>

      {/* Right Login Card Side */}
      <main className="card-side">
        <div className="login-card">
          <div className="card-header">
            <h1>Sign In to Portal</h1>
            <p>Access order tracking, wholesale pricing, and active quote requests.</p>
          </div>

          {message && (
            <div style={{
              padding: '10px 14px',
              borderRadius: '8px',
              marginBottom: '16px',
              fontSize: '13px',
              background: message.type === 'error' ? '#FDF2F2' : '#EFF8F2',
              color: message.type === 'error' ? '#A82B1D' : '#1E6B39',
              border: `1px solid ${message.type === 'error' ? '#F5C6CB' : '#C3E6CB'}`
            }}>
              {message.text}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="form-group">
              <label htmlFor="reactIdentifier">Email or Username</label>
              <div className="input-box">
                <Mail size={18} color="#9C9389" />
                <input
                  id="reactIdentifier"
                  type="text"
                  placeholder="Enter your email or username"
                  value={identifier}
                  onChange={(e) => setIdentifier(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-group">
              <label htmlFor="reactPassword">Password</label>
              <div className="input-box">
                <Lock size={18} color="#9C9389" />
                <input
                  id="reactPassword"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  style={{ background: 'transparent', border: 'none', cursor: 'pointer', display: 'flex' }}
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={18} color="#6B635B" /> : <Eye size={18} color="#6B635B" />}
                </button>
              </div>
            </div>

            <div className="aux-row">
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={rememberMe}
                  onChange={(e) => setRememberMe(e.target.checked)}
                  style={{ accentColor: '#A82B1D' }}
                />
                Remember me
              </label>
              <a href="#" onClick={(e) => { e.preventDefault(); alert('Password reset link will be sent to your registered email.'); }}>
                Forgot password?
              </a>
            </div>

            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? 'Authenticating...' : (
                <>
                  <span>Sign In to Portal</span>
                  <ArrowRight size={18} />
                </>
              )}
            </button>

            <div className="demo-chip">
              <div><span>Demo: </span><code>trade@balajiingredients.com</code></div>
              <button type="button" className="demo-btn" onClick={handleQuickFill}>Fill</button>
            </div>
          </form>

          <div style={{ marginTop: '20px', textAlign: 'center', fontSize: '13px', color: '#6B635B' }}>
            New enterprise client? <a href="#contact" onClick={() => { window.location.hash = ''; }} style={{ color: '#A82B1D', fontWeight: 700 }}>Create B2B Account</a>
          </div>

          <div style={{ marginTop: '16px', textAlign: 'center', fontSize: '10.5px', color: '#9C9389', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '5px' }}>
            <ShieldCheck size={14} color="#D4A343" />
            <span>256-Bit SSL Encrypted Enterprise Gateway</span>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Login;
