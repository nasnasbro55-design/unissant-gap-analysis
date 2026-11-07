import React from 'react';

export default function DisclaimerBanner({ disclaimer }) {
  return (
    <div className="disclaimer-banner" role="alert">
      <div className="disclaimer-icon">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
      </div>
      <div className="disclaimer-text">
        <strong>Official Review Guardrail: </strong>
        {disclaimer || "Flags missing documentation only. It does not judge the case or suggest charges. A person reviews every result."}
      </div>
      <div className="disclaimer-tag">
        Human-in-the-Loop Required
      </div>
    </div>
  );
}
