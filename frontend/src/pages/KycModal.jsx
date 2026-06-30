import React, { useState } from 'react';
import styles from './KycModal.module.css';

export default function KycModal({ onVerify }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [aadhaar, setAadhaar] = useState('');
  const [showNotice, setShowNotice] = useState(true);

  const handleSendOtp = () => {
    if (phone.length >= 10) {
      setLoading(true);
      setTimeout(() => {
        setLoading(false);
        setStep(2);
      }, 1200);
    }
  };

  const handleVerify = () => {
    if (otp.length >= 4 && aadhaar.length >= 12) {
      setLoading(true);
      setTimeout(() => {
        setLoading(false);
        onVerify();
      }, 2000);
    }
  };

  return (
    <>
      {showNotice && (
        <div className={styles.noticeOverlay}>
          <div className={styles.noticeModal}>
            <button className={styles.closeBtn} onClick={() => setShowNotice(false)}>×</button>
            <div className={styles.noticeIcon}>📱</div>
            <h3 className={styles.noticeTitle}>WhatsApp Prototype Notice</h3>
            <p className={styles.noticeBody}>
              This portal can also be accessed via WhatsApp by contacting <strong>+1 (415) 523-8886</strong>. 
              <br/><br/>
              Due to hackathon prototype limitations, we can only facilitate <strong>text-based messages</strong> in WhatsApp. For <strong>voice access</strong> and full functionality, please continue to the web portal.
            </p>
            <button className={styles.continueBtn} onClick={() => setShowNotice(false)}>
              Continue to Portal
            </button>
          </div>
        </div>
      )}

      <div className={styles.overlay} style={{ display: showNotice ? 'none' : 'flex' }}>
        <div className={styles.modal}>
          <div className={styles.icon}>🛡️</div>
          <h2 className={styles.title}>Suraksha Chakra e-KYC</h2>

          {step === 1 ? (
            <>
              <p className={styles.subtitle}>
                Secure your account and protect your rights. Please enter your mobile number.
              </p>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Mobile Number</label>
                <input
                  type="tel"
                  className={styles.input}
                  placeholder="10-digit mobile number"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value.replace(/\D/g, ''))}
                  maxLength={10}
                />
              </div>
              <button
                className={styles.button}
                onClick={handleSendOtp}
                disabled={loading || phone.length < 10}
              >
                {loading ? (
                  <><span className={styles.spinner}></span> Sending OTP...</>
                ) : (
                  'Send OTP'
                )}
              </button>
            </>
          ) : (
            <>
              <p className={styles.subtitle}>
                Enter the OTP sent to +91 {phone} and your Aadhaar number to verify your identity.
              </p>
              <div className={styles.inputGroup}>
                <label className={styles.label}>OTP</label>
                <input
                  type="text"
                  className={styles.input}
                  placeholder="Enter 4-digit OTP"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  maxLength={4}
                />
              </div>
              <div className={styles.inputGroup}>
                <label className={styles.label}>Aadhaar Number</label>
                <input
                  type="text"
                  className={styles.input}
                  placeholder="12-digit Aadhaar Number"
                  value={aadhaar}
                  onChange={(e) => setAadhaar(e.target.value.replace(/\D/g, ''))}
                  maxLength={12}
                />
              </div>
              <button
                className={styles.button}
                onClick={handleVerify}
                disabled={loading || otp.length < 4 || aadhaar.length < 12}
              >
                {loading ? (
                  <><span className={styles.spinner}></span> Verifying with UIDAI...</>
                ) : (
                  'Verify Identity'
                )}
              </button>
            </>
          )}

          <div className={styles.infoPanel}>
            <h4 className={styles.infoTitle}>Registration & Identity Verification</h4>
            <p className={styles.infoBody}>
              To prevent fake complaints and ensure genuine reporting, identity verification is required during registration. Due to digital illiteracy, registration can also be facilitated through Common Service Centres (CSC) and Aadhaar-enabled service centres. This process helps protect contractors from fraudulent reporting.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
