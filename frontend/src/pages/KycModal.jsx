import React, { useState } from 'react';
import styles from './KycModal.module.css';

export default function KycModal({ onVerify }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [aadhaar, setAadhaar] = useState('');

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
    <div className={styles.overlay}>
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
      </div>
    </div>
  );
}
