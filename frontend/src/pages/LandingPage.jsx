import React, { useState } from 'react';
import styles from './LandingPage.module.css';

// Component that renders an image if available, else a dashed placeholder
const AssetImage = ({ src, alt, className, text }) => {
  const [error, setError] = useState(false);

  if (error) {
    return (
      <div className={`${className} ${styles.placeholder}`}>
        <span>Drop {text} here</span>
      </div>
    );
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setError(true)}
    />
  );
};

export default function LandingPage({ onNavigate }) {
  return (
    <div className={styles.container}>
      {/* Top Nav (Visual Only) */}
      <nav className={styles.navbar}>
        <div className={styles.navLogo}>
          <AssetImage src="/assets/logo.png" alt="Logo" className={styles.logoIcon} text="logo.png" />
          <div className={styles.logoText}>
            <div>SURAKSHA</div>
            <div>CHAKRA AI</div>
          </div>
        </div>
        <div className={styles.navLinks}>
          <a href="#" className={styles.activeLink} onClick={(e) => e.preventDefault()}>Home</a>
          <a href="#" onClick={(e) => e.preventDefault()}>About</a>
        </div>
      </nav>

      <main className={styles.main}>
        <div className={styles.heroSection}>
          <h1 className={styles.heroTitle}>SURAKSHA CHAKRA AI SYSTEM</h1>
          <p className={styles.heroSubtitle}>
            AI-powered platform for protecting migrant workers, disaster-displaced families, and vulnerable communities through predictive intelligence.
          </p>
          <div className={styles.languageBadge}>
            <span className={styles.globeIcon}>🌐</span> Available in your <span className={styles.highlight}>regional languages</span>
          </div>
        </div>

        {/* Hero Background Images */}
        <div className={styles.heroImagesContainer}>
          <AssetImage src="/assets/hero-main.jpg" alt="Hero Main" className={styles.heroMainImage} text="hero-main.jpg" />
        </div>

        {/* Portal Cards */}
        <div className={styles.cardsGrid}>
          {/* Card 1: Labour Intelligence */}
          <div className={`${styles.card} ${styles.cardLabour}`}>
            <div className={styles.cardHeader}>
              <div className={`${styles.cardIconWrapper} ${styles.iconLabour}`}>
                <AssetImage src="/assets/labour.png" alt="Labour" className={styles.cardIcon} text="labour.png" />
              </div>
              <h2 className={styles.cardTitle}>LABOUR<br/>INTELLIGENCE PLATFORM</h2>
            </div>
            <ul className={styles.featureList}>
              <li><span className={`${styles.check} ${styles.checkLabour}`}>✓</span> Check fair wages</li>
              <li><span className={`${styles.check} ${styles.checkLabour}`}>✓</span> Voice/Text complaint registration</li>
              <li><span className={`${styles.check} ${styles.checkLabour}`}>✓</span> Contractor risk verification</li>
              <li><span className={`${styles.check} ${styles.checkLabour}`}>✓</span> Legal notice generation</li>
            </ul>
            
            <div className={styles.prototypeBox}>
              <div className={styles.prototypeLabel}>Prototype Access</div>
              <div className={styles.prototypeValue}>WhatsApp (Text Prototype)<br/>+1 (415) 523-8886</div>
            </div>

            <button className={`${styles.cardBtn} ${styles.btnLabour}`} onClick={() => onNavigate('chat')}>
              Open Platform <span>→</span>
            </button>
            <div className={styles.cardFooter}>
              <strong>For Workers & Migrant Families</strong>
              <p>Access all services directly through this web portal or WhatsApp.</p>
            </div>
          </div>

          {/* Card 2: NGO Dashboard */}
          <div className={`${styles.card} ${styles.cardNgo}`}>
            <div className={styles.cardHeader}>
              <div className={`${styles.cardIconWrapper} ${styles.iconNgo}`}>
                <AssetImage src="/assets/ngo.png" alt="NGO" className={styles.cardIcon} text="ngo.png" />
              </div>
              <h2 className={styles.cardTitle}>NGO<br/>DASHBOARD</h2>
            </div>
            <ul className={styles.featureList}>
              <li><span className={`${styles.check} ${styles.checkNgo}`}>✓</span> Vulnerability forecasting</li>
              <li><span className={`${styles.check} ${styles.checkNgo}`}>✓</span> Disaster early warning</li>
              <li><span className={`${styles.check} ${styles.checkNgo}`}>✓</span> Trafficking risk prediction</li>
              <li><span className={`${styles.check} ${styles.checkNgo}`}>✓</span> Resource deployment planning</li>
            </ul>
            
            <div className={styles.spacer}></div>

            <button className={`${styles.cardBtn} ${styles.btnNgo}`} onClick={() => onNavigate('dashboard')}>
              Open Dashboard <span>→</span>
            </button>
            <div className={styles.cardFooter}>
              <strong>For NGOs & Field Organizations</strong>
              <p>Designed for NGOs to identify vulnerable districts before exploitation begins.</p>
            </div>
          </div>

          {/* Card 3: Officer Dashboard */}
          <div className={`${styles.card} ${styles.cardOfficer}`}>
            <div className={styles.cardHeader}>
              <div className={`${styles.cardIconWrapper} ${styles.iconOfficer}`}>
                <AssetImage src="/assets/officer.png" alt="Officer" className={styles.cardIcon} text="officer.png" />
              </div>
              <h2 className={styles.cardTitle}>OFFICER<br/>DASHBOARD</h2>
            </div>
            <ul className={styles.featureList}>
              <li><span className={`${styles.check} ${styles.checkOfficer}`}>✓</span> Labour complaint analytics</li>
              <li><span className={`${styles.check} ${styles.checkOfficer}`}>✓</span> High-risk contractor monitoring</li>
              <li><span className={`${styles.check} ${styles.checkOfficer}`}>✓</span> District-level enforcement insights</li>
              <li><span className={`${styles.check} ${styles.checkOfficer}`}>✓</span> Decision support analytics</li>
            </ul>
            
            <div className={styles.spacer}></div>

            <button className={`${styles.cardBtn} ${styles.btnOfficer}`} onClick={() => onNavigate('dashboard')}>
              Open Dashboard <span>→</span>
            </button>
            <div className={styles.cardFooter}>
              <strong>For Labour Departments & Authorities</strong>
              <p>Supports labour authorities with actionable intelligence and district-level monitoring.</p>
            </div>
          </div>
        </div>

        {/* Bottom Banner */}
        <div className={styles.bottomBanner}>
          <div className={styles.bannerImageWrapper}>
            <AssetImage src="/assets/hero-side.jpg" alt="Disaster" className={styles.bannerImage} text="hero-side.jpg" />
          </div>
          <div className={styles.bannerContent}>
            <h3>Every disaster creates a window of exploitation.<br/>
            <span className={styles.bannerHighlight}>Suraksha Chakra AI helps close it.</span></h3>
            <p>Predict. Prevent. Protect. Empower.</p>
          </div>
        </div>

        <div className={styles.footerLinks}>
          <span><span className={styles.footerIcon}>♡</span> Protecting Workers</span>
          <span className={styles.footerSeparator}>|</span>
          <span><span className={styles.footerIcon}>🛡</span> Preventing Trafficking</span>
          <span className={styles.footerSeparator}>|</span>
          <span><span className={styles.footerIcon}>👥</span> Empowering Communities</span>
          <span className={styles.footerSeparator}>|</span>
          <span><span className={styles.footerIcon}>⚖</span> Enabling Justice</span>
        </div>
      </main>
    </div>
  );
}
