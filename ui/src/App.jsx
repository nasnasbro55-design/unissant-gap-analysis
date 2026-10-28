import React, { useState, useEffect } from 'react';
import DisclaimerBanner from './components/DisclaimerBanner';
import NarrativeViewer from './components/NarrativeViewer';
import ChargeCard from './components/ChargeCard';
import sampleReport from './data/sample_report.json';
import { DEMO_PRESETS } from './data/demo_reports';

export default function App() {
  const [report, setReport] = useState(sampleReport);
  const [selectedPresetId, setSelectedPresetId] = useState('sample_unissant');
  const [activeSentenceIds, setActiveSentenceIds] = useState([]);
  const [activeQuotes, setActiveQuotes] = useState([]);
  const [activeFactKey, setActiveFactKey] = useState(null);
  const [selectedSentenceId, setSelectedSentenceId] = useState(null);
  
  // Custom input state
  const [isCustomModalOpen, setIsCustomModalOpen] = useState(false);
  const [customNarrative, setCustomNarrative] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [apiError, setApiError] = useState(null);

  // Switch demo preset
  const handlePresetChange = (presetId) => {
    setSelectedPresetId(presetId);
    clearHighlights();
    const preset = DEMO_PRESETS.find(p => p.id === presetId);
    if (preset) {
      setReport(preset.data);
    }
  };

  // Hovering on a fact highlights its sentence and quote
  const handleHoverFact = (sentenceIds = [], quote = '') => {
    setActiveSentenceIds(sentenceIds || []);
    setActiveQuotes(quote ? [quote] : []);
  };

  const handleLeaveFact = () => {
    // If a fact was pinned via click, keep it; otherwise clear
    if (!activeFactKey) {
      setActiveSentenceIds([]);
      setActiveQuotes([]);
    }
  };

  // Clicking on a fact pins it
  const handleSelectFact = (factKey, sentenceIds = [], quote = '') => {
    if (activeFactKey === factKey) {
      // Toggle off
      setActiveFactKey(null);
      setActiveSentenceIds([]);
      setActiveQuotes([]);
    } else {
      setActiveFactKey(factKey);
      setActiveSentenceIds(sentenceIds || []);
      setActiveQuotes(quote ? [quote] : []);
    }
  };

  // Clicking on a sentence in narrative
  const handleSentenceClick = (sentenceId) => {
    if (selectedSentenceId === sentenceId) {
      setSelectedSentenceId(null);
    } else {
      setSelectedSentenceId(sentenceId);
      // Find all facts connected to this sentence
      const matchingFacts = [];
      (report.charges || []).forEach(ch => {
        (ch.facts || []).forEach(f => {
          if (f.sentence_ids && f.sentence_ids.includes(sentenceId)) {
            matchingFacts.push(f.quote);
          }
        });
      });
      setActiveQuotes(matchingFacts);
      setActiveSentenceIds([sentenceId]);
    }
  };

  const clearHighlights = () => {
    setActiveSentenceIds([]);
    setActiveQuotes([]);
    setActiveFactKey(null);
    setSelectedSentenceId(null);
  };

  // Submit custom narrative to backend POST /review
  const handleAnalyzeCustom = async () => {
    if (!customNarrative.trim()) return;
    setIsLoading(true);
    setApiError(null);
    try {
      const response = await fetch('/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ narrative: customNarrative })
      });

      if (!response.ok) {
        throw new Error(`API responded with status ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setReport(data);
      setSelectedPresetId('custom');
      setIsCustomModalOpen(false);
      clearHighlights();
    } catch (err) {
      console.warn('Backend /review not reachable or error occurred:', err);
      setApiError(`Could not reach backend API (${err.message}). Is Ethan's backend running on http://localhost:8000? You can continue testing with the built-in preset cases.`);
    } finally {
      setIsLoading(false);
    }
  };

  // Compute summary stats
  const totalCharges = report.charges?.length || 0;
  const completeCount = report.charges?.filter(c => c.status === 'complete').length || 0;
  const gapsCount = report.charges?.filter(c => c.status === 'gaps').length || 0;
  const humanReviewCount = report.charges?.filter(c => c.status === 'human_review').length || 0;
  const totalMissingFacts = report.charges?.reduce((acc, c) => acc + (c.missing?.length || 0), 0) || 0;

  return (
    <div className="app-container">
      {/* Top Navigation / Brand */}
      <header className="app-header">
        <div className="header-brand">
          <div className="brand-logo">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
              <polyline points="9 12 11 14 15 10"></polyline>
            </svg>
          </div>
          <div>
            <h1 className="brand-title">CBP Investigative Narrative Gap Analysis</h1>
            <p className="brand-subtitle">Challenge+X · Unissant UC3 · Team TNUX (Rules-as-Code Engine)</p>
          </div>
        </div>

        <div className="header-controls">
          <div className="preset-selector-box">
            <label htmlFor="preset-select">Active Case:</label>
            <select
              id="preset-select"
              value={selectedPresetId}
              onChange={(e) => handlePresetChange(e.target.value)}
              className="select-preset"
            >
              {DEMO_PRESETS.map(p => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
              {selectedPresetId === 'custom' && (
                <option value="custom">Custom Live Review</option>
              )}
            </select>
          </div>

          <button
            className="btn-primary"
            onClick={() => setIsCustomModalOpen(true)}
            title="Paste or enter a new narrative to review"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Review New Narrative
          </button>
        </div>
      </header>

      {/* Mandatory Disclaimer Banner */}
      <DisclaimerBanner disclaimer={report.disclaimer} />

      {/* System Metrics Bar */}
      <div className="metrics-bar">
        <div className="metric-chip">
          <span className="metric-label">Model</span>
          <span className="metric-value font-mono">{report.model || 'gpt-oss-20b'}</span>
        </div>
        <div className="metric-chip">
          <span className="metric-label">Prompt</span>
          <span className="metric-value font-mono">{report.prompt_version || 'v4'}</span>
        </div>
        <div className="metric-chip">
          <span className="metric-label">Review Latency</span>
          <span className="metric-value font-mono">{report.seconds ? `${report.seconds}s` : '< 6s'}</span>
        </div>
        <div className="metric-chip">
          <span className="metric-label">Charges Checked</span>
          <span className="metric-value">{totalCharges}</span>
        </div>
        <div className="metric-chip">
          <span className="metric-label">Gaps Identified</span>
          <span className={`metric-value ${totalMissingFacts > 0 ? 'text-amber' : 'text-green'}`}>
            {totalMissingFacts}
          </span>
        </div>
        <div className="metric-chip">
          <span className="metric-label">Human Review Needed</span>
          <span className={`metric-value ${humanReviewCount > 0 ? 'text-purple' : 'text-slate'}`}>
            {humanReviewCount > 0 ? 'Yes' : 'No'}
          </span>
        </div>

        {(activeSentenceIds.length > 0 || activeFactKey || selectedSentenceId) && (
          <button className="btn-clear-filter" onClick={clearHighlights}>
            ✕ Clear Highlights
          </button>
        )}
      </div>

      {/* Main Workspace Layout */}
      <main className="main-content">
        {/* Left Column: Narrative with Sentence Highlighting */}
        <section className="column-narrative">
          <NarrativeViewer
            sentences={report.sentences || {}}
            activeSentenceIds={activeSentenceIds}
            activeQuotes={activeQuotes}
            onSentenceClick={handleSentenceClick}
            selectedSentenceId={selectedSentenceId}
          />
        </section>

        {/* Right Column: Statutory Charges & Facts Findings */}
        <section className="column-charges">
          <div className="charges-header">
            <div className="charges-title-wrap">
              <h3>Cited Charges & Statutory Findings</h3>
              <p className="charges-subtitle">
                Deterministic rules check every required element against grounded quotes from the narrative.
              </p>
            </div>
            <div className="charges-status-summary">
              {completeCount > 0 && <span className="status-pill status-complete">{completeCount} Complete</span>}
              {gapsCount > 0 && <span className="status-pill status-gaps">{gapsCount} Gaps</span>}
              {humanReviewCount > 0 && <span className="status-pill status-review">{humanReviewCount} Human Review</span>}
            </div>
          </div>

          <div className="charges-list">
            {(!report.charges || report.charges.length === 0) ? (
              <div className="no-charges-card">
                <div className="icon-warning">⚠️</div>
                <h4>No Citations Found in Narrative</h4>
                <p>This case has been automatically routed to human review because no recognizable INA citation was detected.</p>
              </div>
            ) : (
              report.charges.map((charge, idx) => (
                <ChargeCard
                  key={charge.citation || idx}
                  charge={charge}
                  onHoverFact={handleHoverFact}
                  onLeaveFact={handleLeaveFact}
                  activeFactKey={activeFactKey}
                  onSelectFact={handleSelectFact}
                />
              ))
            )}
          </div>
        </section>
      </main>

      {/* Modal for Custom Narrative Input */}
      {isCustomModalOpen && (
        <div className="modal-overlay" onClick={() => setIsCustomModalOpen(false)}>
          <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Analyze Investigative Narrative</h3>
              <button className="btn-close" onClick={() => setIsCustomModalOpen(false)}>✕</button>
            </div>
            <div className="modal-body">
              <p className="modal-desc">
                Paste or write a free-text CBP narrative. The backend endpoint (<code>POST /review</code>) will extract facts using <code>gpt-oss-20b</code> and execute the deterministic gap & contradiction rules.
              </p>
              {apiError && (
                <div className="modal-alert-error">
                  {apiError}
                </div>
              )}
              <textarea
                className="narrative-textarea"
                rows={8}
                placeholder="Example: SUBJECT MARIA ELENA TORRES-VEGA is a native and citizen of Guatemala. Border Patrol agents encountered subject near Hidalgo, TX... Inadmissible under INA 212(a)(6)(A)(i)..."
                value={customNarrative}
                onChange={(e) => setCustomNarrative(e.target.value)}
              />
            </div>
            <div className="modal-footer">
              <button
                className="btn-secondary"
                onClick={() => {
                  setCustomNarrative("INADMISSIBILITY: 'John Doe' a citizen of Mexico. He has never had any documents that would allow him to be, or remain, in the United States legally. 'John Doe' is inadmissible under section 212(a)(6)(A)(i) of the INA, in that he entered the United States at a place not designated by the Attorney General and was not then admitted or paroled after inspection by an immigration officer. Subject is inadmissible under Section 212(A)(9)(A)(I) of the Immigration and Nationality Act, as amended, in that he was previously ordered removed and entered or attempted to enter without being admitted.");
                }}
              >
                Insert Sample Narrative
              </button>
              <div className="modal-footer-right">
                <button
                  className="btn-cancel"
                  onClick={() => setIsCustomModalOpen(false)}
                >
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  onClick={handleAnalyzeCustom}
                  disabled={isLoading || !customNarrative.trim()}
                >
                  {isLoading ? 'Running Gap Analysis...' : 'Run Analysis'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
