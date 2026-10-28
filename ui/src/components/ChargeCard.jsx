import React, { useState } from 'react';

export default function ChargeCard({
  charge,
  onHoverFact,
  onLeaveFact,
  activeFactKey,
  onSelectFact
}) {
  const [collapsed, setCollapsed] = useState(false);

  const getStatusBadge = (status) => {
    switch (status) {
      case 'complete':
        return <span className="status-badge status-complete">✓ Complete</span>;
      case 'gaps':
        return <span className="status-badge status-gaps">⚠ Gaps Detected</span>;
      case 'human_review':
        return <span className="status-badge status-review">👁 Human Review</span>;
      default:
        return <span className="status-badge">{status}</span>;
    }
  };

  const getConfidenceBadge = (confidence) => {
    if (!confidence) return null;
    return (
      <span className={`confidence-badge conf-${confidence}`}>
        {confidence} conf
      </span>
    );
  };

  const {
    citation,
    name,
    source,
    status,
    reason,
    facts = [],
    missing = [],
    conflicts = [],
    disagreed = []
  } = charge;

  const foundFacts = facts.filter(f => f.found);

  return (
    <div className={`charge-card charge-${status || 'default'}`}>
      <div className="charge-card-header" onClick={() => setCollapsed(!collapsed)}>
        <div className="charge-title-section">
          <div className="citation-pill">
            {citation ? `INA § ${citation}` : 'Citation Unspecified'}
          </div>
          <h4 className="charge-name">{name || (citation ? `Statute ${citation}` : 'Unknown Inadmissibility Charge')}</h4>
          {source && <div className="statute-source">{source}</div>}
        </div>
        <div className="charge-header-right">
          {getStatusBadge(status)}
          <button className="btn-collapse" title="Toggle charge details">
            {collapsed ? '▼' : '▲'}
          </button>
        </div>
      </div>

      {!collapsed && (
        <div className="charge-card-content">
          {/* Reason Alert (for Human Review) */}
          {reason && (
            <div className="reason-alert">
              <div className="alert-icon">⚠️</div>
              <div className="alert-content">
                <strong>Human Review Trigger: </strong>
                <span>{reason}</span>
              </div>
            </div>
          )}

          {/* Conflicts Alert */}
          {conflicts && conflicts.length > 0 && (
            <div className="conflicts-alert">
              <div className="alert-title">❌ Contradiction Detected:</div>
              <p className="alert-desc">
                The officer narrative asserts factual statements that legally conflict with this charge:
              </p>
              <ul className="conflicts-list">
                {conflicts.map((c, i) => (
                  <li
                    key={i}
                    className="conflict-item"
                    onMouseEnter={() => onHoverFact && onHoverFact(c.sentence_ids, c.quote)}
                    onMouseLeave={() => onLeaveFact && onLeaveFact()}
                  >
                    <span className="conflict-type">{c.fact_type}:</span>
                    <span className="conflict-quote">"{c.quote}"</span>
                    {c.sentence_ids && c.sentence_ids.map(s => (
                      <span key={s} className="sentence-tag">{s}</span>
                    ))}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Voting Disagreements */}
          {disagreed && disagreed.length > 0 && (
            <div className="disagreed-alert">
              <div className="alert-title">⚖ Multi-Run Voting Disagreement:</div>
              <p>Independent extraction passes disagreed on: <strong>{disagreed.join(', ')}</strong></p>
            </div>
          )}

          {/* Missing Facts (Gaps) Section */}
          <div className="section-block">
            <div className="section-title">
              <span className="indicator-dot dot-gap"></span>
              <h5>Missing Statutory Facts ({missing.length})</h5>
            </div>
            {missing.length === 0 ? (
              <div className="empty-subtext success-subtext">
                ✓ No required facts missing for this charge.
              </div>
            ) : (
              <div className="missing-facts-grid">
                {missing.map((mf, i) => (
                  <div key={i} className="missing-fact-pill">
                    <span className="missing-icon">✕</span>
                    <span className="missing-label">{mf.replace(/_/g, ' ')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Documented Facts Section */}
          <div className="section-block">
            <div className="section-title">
              <span className="indicator-dot dot-found"></span>
              <h5>Documented Evidence & Quotes ({foundFacts.length})</h5>
            </div>
            {foundFacts.length === 0 ? (
              <div className="empty-subtext">No required elements found in narrative.</div>
            ) : (
              <div className="found-facts-list">
                {foundFacts.map((fact, i) => {
                  const factKey = `${citation}-${fact.fact_type}`;
                  const isSelected = activeFactKey === factKey;

                  return (
                    <div
                      key={i}
                      className={`found-fact-row ${isSelected ? 'fact-active' : ''}`}
                      onMouseEnter={() => onHoverFact && onHoverFact(fact.sentence_ids, fact.quote)}
                      onMouseLeave={() => onLeaveFact && onLeaveFact()}
                      onClick={() => onSelectFact && onSelectFact(factKey, fact.sentence_ids, fact.quote)}
                    >
                      <div className="fact-row-header">
                        <div className="fact-label-group">
                          <span className="fact-icon">✓</span>
                          <span className="fact-name">{fact.label || fact.fact_type.replace(/_/g, ' ')}</span>
                        </div>
                        <div className="fact-badges">
                          {fact.sentence_ids && fact.sentence_ids.map(s => (
                            <span key={s} className="sentence-tag" title="Click to view sentence in narrative">
                              {s}
                            </span>
                          ))}
                          {getConfidenceBadge(fact.confidence)}
                        </div>
                      </div>

                      {fact.quote ? (
                        <div className="fact-quote-box">
                          <span className="quote-mark">“</span>
                          <span className="quote-text">{fact.quote}</span>
                          <span className="quote-mark">”</span>
                        </div>
                      ) : (
                        <div className="fact-quote-missing">Grounded quote not extracted</div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
