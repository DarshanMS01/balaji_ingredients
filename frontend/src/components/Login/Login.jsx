import React, { useState, useEffect, useRef } from 'react';
import { 
  Mail, Lock, Phone, User, Eye, EyeOff, ShieldCheck, ArrowLeft, 
  CheckCircle2, AlertCircle, Sparkles, KeyRound, RefreshCw, Image as ImageIcon,
  Check, ArrowRight
} from 'lucide-react';
import './Login.css';

const HD_BACKGROUNDS = [
  { id: 'mill', name: 'Agri Growth & Silos', url: '/images/login_bg.jpg' },
  { id: 'spices', name: 'Estate Spices', url: '/images/market_spices.jpg' },
  { id: 'kitchen', name: 'Processing & Kitchen', url: '/images/kitchen_scene.jpg' },
  { id: 'farm', name: 'Spice Plantations', url: '/images/farm_fields.jpg' },
  { id: 'hero', name: 'Artisan Milling', url: '/images/hero_bg.jpg' },
];

const Login = () => {
  const [activeTab, setActiveTab] = useState('login'); // 'login' | 'register'
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [selectedBg, setSelectedBg] = useState('/images/login_bg.jpg');
  
  // Forgot Password States
  const [forgotStep, setForgotStep] = useState(1); // 1: email/phone, 2: otp, 3: new pass, 4: success
  const [forgotEmail, setForgotEmail] = useState('');
  const [otp, setOtp] = useState(['', '', '', '', '', '']);
  const [generatedOtp, setGeneratedOtp] = useState('');
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes in seconds
  const [resetToken, setResetToken] = useState('');
  
  const otpRefs = useRef([]);

  // Form States
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '', type: '' });
  const [liveOtpBanner, setLiveOtpBanner] = useState(null);
  const [showGoogleModal, setShowGoogleModal] = useState(false);
  
  // Login Form
  const [loginData, setLoginData] = useState({ identifier: '', password: '', rememberMe: false });
  
  // Register Form
  const [registerData, setRegisterData] = useState({
    fullName: '', email: '', phone: '', password: '', confirmPassword: '', agreeTerms: true
  });

  // Calculate Password Strength
  const getPasswordStrength = (pass) => {
    if (!pass) return '';
    let strength = 0;
    if (pass.length >= 8) strength += 1;
    if (pass.match(/[A-Z]/) && pass.match(/[a-z]/)) strength += 1;
    if (pass.match(/[0-9]/)) strength += 1;
    if (pass.match(/[^A-Za-z0-9]/)) strength += 1;
    
    if (strength <= 1) return 'weak';
    if (strength === 2 || strength === 3) return 'medium';
    return 'strong';
  };

  const showToast = (message, type = 'error') => {
    setToast({ show: true, message, type });
    setTimeout(() => setToast({ show: false, message: '', type: '' }), 6000);
  };

  // Google Sign In Initialization
  useEffect(() => {
    if (window.google && window.google.accounts && window.google.accounts.id) {
      try {
        window.google.accounts.id.initialize({
          client_id: "721983021948-balajiingredients.apps.googleusercontent.com",
          callback: handleGoogleResponse,
          auto_select: false,
          cancel_on_tap_outside: true,
        });
        
        const googleBtn = document.getElementById("google-signin-btn-container");
        if (googleBtn && !showForgotPassword) {
          window.google.accounts.id.renderButton(googleBtn, {
            theme: "filled_black",
            size: "large",
            shape: "pill",
            width: "100%",
            text: activeTab === 'login' ? "continue_with" : "signup_with",
            logo_alignment: "center"
          });
        }
      } catch (err) {
        console.warn("Google GSI initialized in fallback mode:", err);
      }
    }
  }, [activeTab, showForgotPassword]);

  const handleGoogleClick = () => {
    if (window.google && window.google.accounts && window.google.accounts.id) {
      try {
        window.google.accounts.id.prompt();
      } catch (e) {
        setShowGoogleModal(true);
      }
    } else {
      setShowGoogleModal(true);
    }
  };

  const handleGoogleResponse = async (response) => {
    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/api/auth/google/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ credential: response.credential || response })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`Welcome ${data.user?.name || 'User'}! Redirecting...`, 'success');
        setTimeout(() => {
          window.location.hash = '#home';
        }, 1200);
      } else {
        showToast(data.message || 'Google authentication failed. Please try again.');
      }
    } catch (err) {
      showToast('Backend server connection error. Ensure Django is running.');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectMockGoogleAccount = (account) => {
    setShowGoogleModal(false);
    handleGoogleResponse({
      email: account.email,
      name: account.name,
      picture: account.avatar
    });
  };

  // Handlers
  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast(`Welcome back, ${data.user?.name || 'Partner'}!`, 'success');
        setTimeout(() => {
          window.location.hash = '#home';
        }, 1000);
      } else {
        showToast(data.message || 'Invalid Phone/Email or Password.');
      }
    } catch (err) {
      showToast('Unable to reach server. Please check your internet connection.');
    } finally {
      setLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (registerData.password !== registerData.confirmPassword) {
      showToast('Passwords do not match. Please re-enter.');
      return;
    }
    if (registerData.password.length < 6) {
      showToast('Password must be at least 6 characters.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(registerData)
      });
      const data = await res.json();
      if (res.ok && data.success) {
        showToast('Registration successful! Welcome to Balaji Ingredients.', 'success');
        setTimeout(() => {
          window.location.hash = '#home';
        }, 1200);
      } else {
        showToast(data.message || 'Registration failed. Email or phone may already exist.');
      }
    } catch (err) {
      showToast('Server connection error. Please verify backend is running.');
    } finally {
      setLoading(false);
    }
  };

  // Forgot Password Countdown Timer
  useEffect(() => {
    let timer;
    if (forgotStep === 2 && timeLeft > 0) {
      timer = setInterval(() => setTimeLeft(prev => prev - 1), 1000);
    }
    return () => clearInterval(timer);
  }, [forgotStep, timeLeft]);

  // Real-time OTP Request
  const handleForgotSubmit = async (e) => {
    if (e) e.preventDefault();
    if (!forgotEmail) {
      showToast('Please enter your registered Phone Number or Email.');
      return;
    }
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/auth/forgot-password/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setGeneratedOtp(data.otp);
        setForgotStep(2);
        setTimeLeft(300);
        setOtp(['', '', '', '', '', '']);
        
        // Real-Time Live OTP Notification Banner
        setLiveOtpBanner({
          code: data.otp,
          target: data.target || forgotEmail,
          time: new Date().toLocaleTimeString()
        });
        showToast(`Real-Time OTP [${data.otp}] generated for ${forgotEmail}!`, 'success');
      } else {
        showToast(data.message || 'Error generating OTP. User not found.');
      }
    } catch (err) {
      showToast('Server error while generating OTP.');
    } finally {
      setLoading(false);
    }
  };

  const handleOtpChange = (index, value) => {
    const val = value.replace(/\D/g, '');
    if (val.length > 1) {
      // If user pastes multi-digit OTP
      const digits = val.slice(0, 6).split('');
      const updated = [...otp];
      digits.forEach((d, i) => {
        if (i < 6) updated[i] = d;
      });
      setOtp(updated);
      if (digits.length === 6) {
        verifyOtp(digits.join(''));
      }
      return;
    }

    const newOtp = [...otp];
    newOtp[index] = val;
    setOtp(newOtp);

    if (val !== '' && index < 5) {
      otpRefs.current[index + 1]?.focus();
    }
    
    // Auto-verify when 6th digit entered
    if (val !== '' && index === 5) {
      const fullCode = newOtp.join('');
      if (fullCode.length === 6) {
        verifyOtp(fullCode);
      }
    }
  };
  
  const handleOtpKeyDown = (index, e) => {
    if (e.key === 'Backspace' && otp[index] === '' && index > 0) {
      otpRefs.current[index - 1]?.focus();
    }
  };

  const autoFillOtp = () => {
    if (generatedOtp && generatedOtp.length === 6) {
      const digits = generatedOtp.split('');
      setOtp(digits);
      verifyOtp(generatedOtp);
    }
  };

  const verifyOtp = async (otpString) => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/auth/verify-otp/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: forgotEmail, otp: otpString })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setResetToken(data.reset_token);
        setForgotStep(3);
        setLiveOtpBanner(null);
        showToast('OTP verified successfully! Set your new password.', 'success');
      } else {
        showToast(data.message || 'Invalid or expired OTP code.');
      }
    } catch (err) {
      showToast('Network error during OTP verification.');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (e) => {
    e.preventDefault();
    const newPass = e.target.newPassword.value;
    const confirmPass = e.target.confirmNewPassword.value;
    
    if (newPass !== confirmPass) {
      showToast('Passwords do not match. Please re-check.');
      return;
    }
    if (newPass.length < 6) {
      showToast('Password must be at least 6 characters.');
      return;
    }
    
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/auth/reset-password/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          email: forgotEmail, 
          reset_token: resetToken, 
          new_password: newPass 
        })
      });
      const data = await res.json();
      if (res.ok && data.success) {
        setForgotStep(4);
        showToast('Password reset successfully!', 'success');
      } else {
        showToast(data.message || 'Error updating password.');
      }
    } catch (err) {
      showToast('Network error while resetting password.');
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div 
      className="transparent-login-viewport" 
      style={{ backgroundImage: `url(${selectedBg})` }}
    >
      {/* Dark Ambient Overlay */}
      <div className="login-backdrop-overlay"></div>

      {/* Top Header Bar */}
      <header className="transparent-login-header">
        <a href="#home" className="header-brand">
          <div className="brand-symbol">B</div>
          <div className="brand-text">
            <span className="brand-name">Balaji Ingredients</span>
            <span className="brand-tagline">ESTATE & STONE-MILLED</span>
          </div>
        </a>

        {/* HD Background Selector Pills */}
        <div className="bg-selector-widget">
          <span className="bg-selector-label"><ImageIcon size={14} /> HD View:</span>
          {HD_BACKGROUNDS.map(bg => (
            <button
              key={bg.id}
              className={`bg-pill ${selectedBg === bg.url ? 'active' : ''}`}
              onClick={() => setSelectedBg(bg.url)}
              title={bg.name}
            >
              {bg.name.split(' ')[0]}
            </button>
          ))}
        </div>

        <a href="#home" className="exit-btn">
          <ArrowLeft size={16} /> Exit to Site
        </a>
      </header>

      {/* Real-Time Live OTP Toast Notification */}
      {liveOtpBanner && (
        <div className="realtime-otp-push-banner">
          <div className="otp-push-header">
            <div className="otp-push-title">
              <span className="live-dot"></span>
              <strong>Real-Time OTP Generated</strong>
            </div>
            <span className="otp-push-time">{liveOtpBanner.time}</span>
          </div>
          <div className="otp-push-body">
            <span>Sent to {liveOtpBanner.target}:</span>
            <div className="otp-highlight-badge">
              <KeyRound size={16} />
              <span className="otp-code-text">{liveOtpBanner.code}</span>
            </div>
          </div>
          <button type="button" className="otp-autofill-btn" onClick={autoFillOtp}>
            <Check size={14} /> One-Click Auto Fill Code
          </button>
        </div>
      )}

      {/* Main Glassmorphism Container */}
      <main className="transparent-login-main">
        {/* Left Side: Editorial Presentation */}
        <div className="editorial-glass-pane">
          <div className="spice-tag">
            <Sparkles size={14} /> 100% PURE & STEAM STERILIZED
          </div>
          <h1 className="editorial-title">
            The Aroma of <br />
            <em>Authentic Spices,</em> <br />
            Engineered for Scale.
          </h1>
          <p className="editorial-desc">
            Directly from South Indian estates — cold stone-ground, batch-tested, and delivered with uncompromised potency.
          </p>
          
          <div className="glass-feature-chips">
            <div className="feature-chip">
              <ShieldCheck size={18} />
              <div>
                <strong>FSSAI & ISO 22000</strong>
                <small>Certified Processing</small>
              </div>
            </div>
            <div className="feature-chip">
              <Sparkles size={18} />
              <div>
                <strong>NABL Lab Tested</strong>
                <small>Every Single Batch</small>
              </div>
            </div>
          </div>
        </div>

        {/* Right Side: 100% Transparent Glassmorphism Card */}
        <div className="frosted-glass-card">
          {/* Toast Message */}
          {toast.show && (
            <div className={`glass-toast ${toast.type === 'success' ? 'toast-success' : 'toast-error'}`}>
              {toast.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
              <span>{toast.message}</span>
            </div>
          )}

          {!showForgotPassword ? (
            <>
              {/* Card Tabs */}
              <div className="glass-tabs-nav">
                <button
                  type="button"
                  className={`glass-tab-btn ${activeTab === 'login' ? 'active' : ''}`}
                  onClick={() => setActiveTab('login')}
                >
                  Sign In
                </button>
                <button
                  type="button"
                  className={`glass-tab-btn ${activeTab === 'register' ? 'active' : ''}`}
                  onClick={() => setActiveTab('register')}
                >
                  Create Account
                </button>
              </div>

              {activeTab === 'login' ? (
                /* Sign In Form */
                <form className="glass-auth-form" onSubmit={handleLoginSubmit}>
                  <div className="glass-field-group">
                    <label className="glass-label">Phone Number or Email</label>
                    <div className="glass-input-wrapper">
                      <User className="glass-input-icon" size={18} />
                      <input
                        type="text"
                        className="glass-input"
                        placeholder="e.g. +91 9876543210 or user@company.com"
                        value={loginData.identifier}
                        onChange={(e) => setLoginData({...loginData, identifier: e.target.value})}
                        required
                      />
                    </div>
                  </div>

                  <div className="glass-field-group">
                    <label className="glass-label">Password</label>
                    <div className="glass-input-wrapper">
                      <Lock className="glass-input-icon" size={18} />
                      <input
                        type={showPassword ? "text" : "password"}
                        className="glass-input"
                        placeholder="Enter your secret password"
                        value={loginData.password}
                        onChange={(e) => setLoginData({...loginData, password: e.target.value})}
                        required
                      />
                      <button
                        type="button"
                        className="glass-pwd-toggle"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <div className="glass-form-row">
                    <label className="glass-checkbox-wrap">
                      <input
                        type="checkbox"
                        checked={loginData.rememberMe}
                        onChange={(e) => setLoginData({...loginData, rememberMe: e.target.checked})}
                      />
                      <span>Remember login</span>
                    </label>
                    <button
                      type="button"
                      className="glass-forgot-btn"
                      onClick={() => {
                        setShowForgotPassword(true);
                        setForgotStep(1);
                      }}
                    >
                      Forgot password?
                    </button>
                  </div>

                  <button type="submit" className="glass-primary-btn" disabled={loading}>
                    {loading ? <span className="glass-spinner"></span> : (
                      <>
                        <span>Sign In to Portal</span>
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>

                  <div className="glass-divider">
                    <span>OR CONTINUE WITH</span>
                  </div>

                  {/* Google Sign In Area */}
                  <div className="google-auth-wrapper">
                    <div id="google-signin-btn-container" style={{ width: '100%' }}></div>
                    <button
                      type="button"
                      className="custom-google-glass-btn"
                      onClick={handleGoogleClick}
                    >
                      <svg className="google-g-svg" viewBox="0 0 24 24">
                        <path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.7l3.1-3.1C17.3 1.8 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.4 9 5 12 5z" />
                        <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z" />
                        <path fill="#FBBC05" d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.8 0-1.3.2-2.1.4-2.8L1.9 6.3C.7 8.7 0 10.8 0 12s.7 3.3 1.9 5.7l3.7-2.9z" />
                        <path fill="#34A853" d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.4-6.4-5.2L1.9 16c1.8 3.7 5.6 7 10.1 7z" />
                      </svg>
                      <span>Continue with Google</span>
                    </button>
                  </div>
                </form>
              ) : (
                /* Register Form */
                <form className="glass-auth-form" onSubmit={handleRegisterSubmit}>
                  <div className="glass-field-group">
                    <label className="glass-label">Full Name</label>
                    <div className="glass-input-wrapper">
                      <User className="glass-input-icon" size={18} />
                      <input
                        type="text"
                        className="glass-input"
                        placeholder="e.g. Ramesh Kumar"
                        value={registerData.fullName}
                        onChange={(e) => setRegisterData({...registerData, fullName: e.target.value})}
                        required
                      />
                    </div>
                  </div>

                  <div className="glass-field-group">
                    <label className="glass-label">Email Address</label>
                    <div className="glass-input-wrapper">
                      <Mail className="glass-input-icon" size={18} />
                      <input
                        type="email"
                        className="glass-input"
                        placeholder="ramesh@enterprises.com"
                        value={registerData.email}
                        onChange={(e) => setRegisterData({...registerData, email: e.target.value})}
                        required
                      />
                    </div>
                  </div>

                  <div className="glass-field-group">
                    <label className="glass-label">Phone Number (with WhatsApp)</label>
                    <div className="glass-input-wrapper">
                      <Phone className="glass-input-icon" size={18} />
                      <input
                        type="tel"
                        className="glass-input"
                        placeholder="+91 98765 43210"
                        value={registerData.phone}
                        onChange={(e) => setRegisterData({...registerData, phone: e.target.value})}
                        required
                      />
                    </div>
                  </div>

                  <div className="glass-field-group">
                    <label className="glass-label">Password</label>
                    <div className="glass-input-wrapper">
                      <Lock className="glass-input-icon" size={18} />
                      <input
                        type={showPassword ? "text" : "password"}
                        className="glass-input"
                        placeholder="Min. 6 characters"
                        value={registerData.password}
                        onChange={(e) => setRegisterData({...registerData, password: e.target.value})}
                        required
                      />
                      <button
                        type="button"
                        className="glass-pwd-toggle"
                        onClick={() => setShowPassword(!showPassword)}
                      >
                        {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                    {registerData.password && (
                      <div className={`glass-strength-meter ${getPasswordStrength(registerData.password)}`}>
                        <div className="strength-track">
                          <div className="strength-fill"></div>
                        </div>
                        <span className="strength-caption">
                          Strength: <strong>{getPasswordStrength(registerData.password).toUpperCase()}</strong>
                        </span>
                      </div>
                    )}
                  </div>

                  <div className="glass-field-group">
                    <label className="glass-label">Confirm Password</label>
                    <div className="glass-input-wrapper">
                      <Lock className="glass-input-icon" size={18} />
                      <input
                        type={showConfirmPassword ? "text" : "password"}
                        className="glass-input"
                        placeholder="Re-type password"
                        value={registerData.confirmPassword}
                        onChange={(e) => setRegisterData({...registerData, confirmPassword: e.target.value})}
                        required
                      />
                      <button
                        type="button"
                        className="glass-pwd-toggle"
                        onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                      >
                        {showConfirmPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                      </button>
                    </div>
                  </div>

                  <label className="glass-checkbox-wrap" style={{ marginTop: '0.25rem' }}>
                    <input
                      type="checkbox"
                      checked={registerData.agreeTerms}
                      onChange={(e) => setRegisterData({...registerData, agreeTerms: e.target.checked})}
                      required
                    />
                    <span>I agree to Balaji Ingredients Terms & Privacy Policy</span>
                  </label>

                  <button type="submit" className="glass-primary-btn" disabled={loading}>
                    {loading ? <span className="glass-spinner"></span> : (
                      <>
                        <span>Create B2B Account</span>
                        <ArrowRight size={18} />
                      </>
                    )}
                  </button>

                  <div className="glass-divider">
                    <span>OR REGISTER WITH</span>
                  </div>

                  <button
                    type="button"
                    className="custom-google-glass-btn"
                    onClick={handleGoogleClick}
                  >
                    <svg className="google-g-svg" viewBox="0 0 24 24">
                      <path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.7l3.1-3.1C17.3 1.8 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.4 9 5 12 5z" />
                      <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z" />
                      <path fill="#FBBC05" d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.8 0-1.3.2-2.1.4-2.8L1.9 6.3C.7 8.7 0 10.8 0 12s.7 3.3 1.9 5.7l3.7-2.9z" />
                      <path fill="#34A853" d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.4-6.4-5.2L1.9 16c1.8 3.7 5.6 7 10.1 7z" />
                    </svg>
                    <span>Sign up with Google</span>
                  </button>
                </form>
              )}
            </>
          ) : (
            /* Forgot Password Flow */
            <div className="glass-forgot-flow">
              {forgotStep === 1 && (
                <div className="forgot-step-pane">
                  <h2 className="step-title">Forgot Password</h2>
                  <p className="step-subtitle">
                    Enter your registered <strong>Phone Number or Email</strong> to generate a real-time 6-digit OTP.
                  </p>
                  <form className="glass-auth-form" onSubmit={handleForgotSubmit}>
                    <div className="glass-field-group">
                      <label className="glass-label">Phone or Email</label>
                      <div className="glass-input-wrapper">
                        <Mail className="glass-input-icon" size={18} />
                        <input
                          type="text"
                          className="glass-input"
                          placeholder="e.g. +91 9876543210 or user@example.com"
                          value={forgotEmail}
                          onChange={(e) => setForgotEmail(e.target.value)}
                          required
                          autoFocus
                        />
                      </div>
                    </div>
                    <button type="submit" className="glass-primary-btn" disabled={loading}>
                      {loading ? <span className="glass-spinner"></span> : (
                        <>
                          <span>Generate Real-Time OTP</span>
                          <KeyRound size={18} />
                        </>
                      )}
                    </button>
                    <button
                      type="button"
                      className="glass-text-link"
                      onClick={() => setShowForgotPassword(false)}
                    >
                      ← Back to Sign In
                    </button>
                  </form>
                </div>
              )}

              {forgotStep === 2 && (
                <div className="forgot-step-pane">
                  <h2 className="step-title">Verify 6-Digit OTP</h2>
                  <p className="step-subtitle">
                    Enter the real-time security code sent for <strong>{forgotEmail}</strong>
                  </p>

                  <div className="realtime-otp-inputs-grid">
                    {otp.map((digit, index) => (
                      <input
                        key={index}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        className="glass-otp-box"
                        value={digit}
                        onChange={(e) => handleOtpChange(index, e.target.value)}
                        onKeyDown={(e) => handleOtpKeyDown(index, e)}
                        ref={(el) => (otpRefs.current[index] = el)}
                        autoFocus={index === 0}
                      />
                    ))}
                  </div>

                  <div className="otp-timer-bar">
                    <span className="timer-count">Expires in: <strong>{formatTime(timeLeft)}</strong></span>
                    <button
                      type="button"
                      className="resend-otp-btn"
                      disabled={timeLeft > 0 || loading}
                      onClick={() => handleForgotSubmit()}
                    >
                      <RefreshCw size={14} /> Resend OTP
                    </button>
                  </div>

                  <button
                    type="button"
                    className="glass-primary-btn"
                    disabled={otp.join('').length < 6 || loading}
                    onClick={() => verifyOtp(otp.join(''))}
                  >
                    {loading ? <span className="glass-spinner"></span> : (
                      <>
                        <span>Verify & Continue</span>
                        <Check size={18} />
                      </>
                    )}
                  </button>

                  <button
                    type="button"
                    className="glass-text-link"
                    onClick={() => setForgotStep(1)}
                  >
                    ← Change Phone/Email
                  </button>
                </div>
              )}

              {forgotStep === 3 && (
                <div className="forgot-step-pane">
                  <h2 className="step-title">Create New Password</h2>
                  <p className="step-subtitle">
                    Set a secure password for your Balaji Ingredients account.
                  </p>
                  <form className="glass-auth-form" onSubmit={handleResetPassword}>
                    <div className="glass-field-group">
                      <label className="glass-label">New Password</label>
                      <div className="glass-input-wrapper">
                        <Lock className="glass-input-icon" size={18} />
                        <input
                          type="password"
                          name="newPassword"
                          className="glass-input"
                          placeholder="Min. 6 characters"
                          required
                          minLength={6}
                          autoFocus
                        />
                      </div>
                    </div>
                    <div className="glass-field-group">
                      <label className="glass-label">Confirm New Password</label>
                      <div className="glass-input-wrapper">
                        <Lock className="glass-input-icon" size={18} />
                        <input
                          type="password"
                          name="confirmNewPassword"
                          className="glass-input"
                          placeholder="Re-enter new password"
                          required
                          minLength={6}
                        />
                      </div>
                    </div>
                    <button type="submit" className="glass-primary-btn" disabled={loading}>
                      {loading ? <span className="glass-spinner"></span> : (
                        <>
                          <span>Save & Update Password</span>
                          <Check size={18} />
                        </>
                      )}
                    </button>
                  </form>
                </div>
              )}

              {forgotStep === 4 && (
                <div className="forgot-step-pane success-state">
                  <div className="success-halo-icon">
                    <CheckCircle2 size={42} />
                  </div>
                  <h2 className="step-title">Password Reset Complete!</h2>
                  <p className="step-subtitle">
                    Your password has been updated. You can now access your corporate dashboard.
                  </p>
                  <button
                    type="button"
                    className="glass-primary-btn"
                    onClick={() => {
                      setShowForgotPassword(false);
                      setForgotStep(1);
                      setActiveTab('login');
                    }}
                  >
                    <span>Proceed to Sign In</span>
                    <ArrowRight size={18} />
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Google Account Selector Dialog */}
      {showGoogleModal && (
        <div className="google-modal-backdrop" onClick={() => setShowGoogleModal(false)}>
          <div className="google-modal-card" onClick={(e) => e.stopPropagation()}>
            <div className="google-modal-header">
              <svg className="google-g-svg-large" viewBox="0 0 24 24">
                <path fill="#EA4335" d="M12 5c1.6 0 3 .6 4.1 1.7l3.1-3.1C17.3 1.8 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.4 9 5 12 5z" />
                <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z" />
                <path fill="#FBBC05" d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.8 0-1.3.2-2.1.4-2.8L1.9 6.3C.7 8.7 0 10.8 0 12s.7 3.3 1.9 5.7l3.7-2.9z" />
                <path fill="#34A853" d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.4-6.4-5.2L1.9 16c1.8 3.7 5.6 7 10.1 7z" />
              </svg>
              <h3>Choose a Google Account</h3>
              <p>to continue to <strong>Balaji Ingredients</strong></p>
            </div>
            <div className="google-accounts-list">
              {[
                { name: 'Chandan Kumar', email: 'chandan.balaji@gmail.com', avatar: 'C' },
                { name: 'Balaji Enterprise Admin', email: 'admin@balajiingredients.com', avatar: 'B' },
                { name: 'Sourcing Procurement', email: 'procure@spicesouth.in', avatar: 'S' },
              ].map((acc, idx) => (
                <button
                  key={idx}
                  type="button"
                  className="google-account-item"
                  onClick={() => handleSelectMockGoogleAccount(acc)}
                >
                  <div className="acc-avatar">{acc.avatar}</div>
                  <div className="acc-info">
                    <strong>{acc.name}</strong>
                    <span>{acc.email}</span>
                  </div>
                </button>
              ))}
            </div>
            <button
              type="button"
              className="google-modal-close"
              onClick={() => setShowGoogleModal(false)}
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default Login;
