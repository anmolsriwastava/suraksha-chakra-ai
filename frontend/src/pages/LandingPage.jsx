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
      
      {/* Cinematic Hero Background */}
      <div className={styles.heroBackground}>
        <AssetImage src="/assets/hero-main.jpg" alt="Hero Background" className={styles.heroMainImage} text="hero-main.jpg" />
        <div className={styles.heroOverlay}></div>
      </div>

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

      {/* Hero Content Section */}
      <header className={styles.heroSection}>
        <div className={styles.heroContent}>
          <h1 className={styles.heroTitle}>SURAKSHA CHAKRA AI SYSTEM</h1>

          <hr className={styles.heroDivider} />
          <p className={styles.heroSubtitle}>
            AI-powered platform for protecting migrant workers, disaster-displaced families, and vulnerable communities through predictive intelligence.
          </p>
          <div className={styles.languageBadge}>
            <span className={styles.globeIcon}>🌐</span> Available in 22+ Indian Languages via Voice & Text
          </div>
        </div>
      </header>

      {/* Main Content (Cards) */}
      <main className={styles.main}>
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
              <li><span className={styles.bullet}>•</span> AI Wage Verification</li>
              <li><span className={styles.bullet}>•</span> Anonymous Voice & Text Complaints</li>
              <li><span className={styles.bullet}>•</span> Check Contractor Risk Before Joining</li>
              <li><span className={styles.bullet}>•</span> Anonymous Legal Notice Generation</li>
            </ul>
            
            <div className={styles.glassInnerCard}>
              <div className={styles.glassInnerHeader}>Prototype Access</div>
              <div className={styles.glassInnerRow}>
                <span className={styles.glassInnerLabel}>Web Portal</span>
              </div>
              <div className={styles.glassInnerRow}>
                <span className={styles.glassInnerLabel}>WhatsApp (Text Prototype)</span>
                <span className={styles.glassInnerValue}>+1 (415) 523-8886</span>
              </div>
            </div>

            <button className={`${styles.cardBtn} ${styles.btnLabour}`} onClick={() => onNavigate('chat')}>
              Open Platform
            </button>
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
              <li><span className={styles.bullet}>•</span> District Risk Forecasting</li>
              <li><span className={styles.bullet}>•</span> Disaster Displacement Monitoring</li>
              <li><span className={styles.bullet}>•</span> Trafficking Early Warning</li>
              <li><span className={styles.bullet}>•</span> Resource Deployment Planning</li>
            </ul>
            
            <div className={styles.spacer}></div>

            <button className={`${styles.cardBtn} ${styles.btnNgo}`} onClick={() => onNavigate('dashboard')}>
              Open Dashboard
            </button>
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
              <li><span className={styles.bullet}>•</span> Complaint Intelligence</li>
              <li><span className={styles.bullet}>•</span> High-Risk Contractor Monitoring</li>
              <li><span className={styles.bullet}>•</span> District Vulnerability Analytics</li>
              <li><span className={styles.bullet}>•</span> Policy Decision Support</li>
            </ul>
            
            <div className={styles.spacer}></div>

            <button className={`${styles.cardBtn} ${styles.btnOfficer}`} onClick={() => onNavigate('labour-officer')}>
              Open Dashboard
            </button>
          </div>
        </div>

      </main>

      {/* Cinematic Storytelling Chapter */}
      <section className={styles.storySection}>
        <div className={styles.storyBackground}>
          <AssetImage src="/assets/hero-side.jpg" alt="Disaster" className={styles.storyImage} text="hero-side.jpg" />
          <div className={styles.storyOverlay}></div>
        </div>
        <div className={styles.storyContentWrapper}>
          <div className={styles.storyContent}>
            <h3 className={styles.storyTitle}>
              Every disaster creates a window of exploitation.
            </h3>
            <span className={styles.storyHighlight}>Suraksha Chakra AI helps close it.</span>

          </div>
        </div>
      </section>

      {/* How Our Intelligence Works (Pipeline) */}
      <section className={styles.pipelineSection}>
        <h2 className={styles.pipelineSectionTitle}>How Our Intelligence Works</h2>
        <div className={styles.pipelineImageWrapper}>
          <AssetImage 
            src="/assets/data-pipeline.png" 
            alt="Data Intelligence Architecture Pipeline" 
            className={styles.pipelineImage} 
            text="data-pipeline.png" 
          />
        </div>
      </section>

      <footer className={styles.footerLinks}>
        <span><span className={styles.footerIcon}>♡</span> Protecting Workers</span>
        <span className={styles.footerSeparator}>|</span>
        <span><span className={styles.footerIcon}>🛡</span> Preventing Trafficking</span>
        <span className={styles.footerSeparator}>|</span>
        <span><span className={styles.footerIcon}>👥</span> Empowering Communities</span>
        <span className={styles.footerSeparator}>|</span>
        <span><span className={styles.footerIcon}>⚖</span> Enabling Justice</span>
      </footer>
    </div>
  );
}
