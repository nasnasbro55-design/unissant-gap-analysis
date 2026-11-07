import React, { useState, useEffect, useRef } from 'react';
import DisclaimerBanner from './components/DisclaimerBanner';
import NarrativeViewer from './components/NarrativeViewer';
import ChargeCard from './components/ChargeCard';
import sampleReport from './data/sample_report.json';
import { DEMO_PRESETS } from './data/demo_reports';

const LIVE_API_URL = 'http://localhost:8000/review';

export default function App() {
  const [report, setReport] = useState(sampleReport);
  const [selectedPresetId, setSelectedPresetId] = useState('sample_unissant');
  const [activeSentenceIds, setActiveSentenceIds] = useState([]);
  const [activeQuotes, setActiveQuotes] = useState([]);
  const [activeFactKey, setActiveFactKey] = useState(null);
  const [selectedSentenceId, setSelectedSentenceId] = useState(null);
  
  // Live input & API state
  const [showLiveEditor, setShowLiveEditor] = useState(false);
  const [narrativeInput, setNarrativeInput] = useState(
    "INADMISSIBILITY: 'John Doe' a citizen of Mexico. He has never had any documents that would allow him to be, or remain, in the United States legally. 'John Doe' is inadmissible under section 212(a) (6) (A) (i) of the INA, in that he entered the United States at a place not designated by the Attorney General and was not then admitted or paroled after inspection by an immigration officer. INADMISSIBILITY: Subject is inadmissible under Section 212(A) (9) (A) (I) of the Immigration and Nationality Act, as amended, in that he was previously ordered removed and entered or attempted to enter without being admitted."
  );
  const [isLoading, setIsLoading] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [apiError, setApiError] = useState(null);
  const timerRef = useRef(null);

  // Timer for loading state
  useEffect(() => {
    if (isLoading) {
      setElapsedSeconds(0);
      timerRef.current = setInterval(() => {
        setElapsedSeconds(prev => +(prev + 0.1).toFixed(1));
      }, 100);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isLoading]);

  // Switch demo preset
  const handlePresetChange = (presetId) => {
    setSelectedPresetId(presetId);
    setApiError(null);
    clearHighlights();
    const preset = DEMO_PRESETS.find(p => p.id === presetId);
    if (preset) {
      setReport(preset.data);
      // Also update narrative editor with this preset's sentences
      const fullText = Object.values(preset.data.sentences || {}).join(' ');
      setNarrativeInput(fullText);
    }
  };

  // Hovering on a fact highlights its sentence and quote
  const handleHoverFact = (sentenceIds = [], quote = '') => {
    setActiveSentenceIds(sentenceIds || []);
    setActiveQuotes(quote ? [quote] : []);
  };

  const handleLeaveFact = () => {
    if (!activeFactKey) {
      setActiveSentenceIds([]);
      setActiveQuotes([]);
    }
  };

  // Clicking on a fact pins it
  const handleSelectFact = (factKey, sentenceIds = [], quote = '') => {
    if (activeFactKey === factKey) {
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
      const matchingQuotes = [];
      (report.charges || []).forEach(ch => {
        (ch.facts || []).forEach(f => {
          if (f.sentence_ids && f.sentence_ids.includes(sentenceId) && f.quote) {
            matchingQuotes.push(f.quote);
          }
        });
      });
      setActiveQuotes(matchingQuotes);
      setActiveSentenceIds([sentenceId]);
    }
  };

  const clearHighlights = () => {
    setActiveSentenceIds([]);
    setActiveQuotes([]);
    setActiveFactKey(null);
    setSelectedSentenceId(null);
  };

  // POST narrative to Ethan's live backend: http://localhost:8000/review
  const handleRunLiveReview = async () => {
    if (!narrativeInput.trim()) return;
    setIsLoading(true);
    setApiError(null);
    clearHighlights();

    try {
      let response;
      try {
        // Direct call to Ethan's backend
        response = await fetch(LIVE_API_URL, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ narrative: narrativeInput })
        });
      } catch (directErr) {
        // Fallback to Vite proxy (/review)
        response = await fetch('/review', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ narrative: narrativeInput })
        });
      }

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setReport(data);
      setSelectedPresetId('custom_live');
      setShowLiveEditor(false);
    } catch (err) {
      console.error('API /review request error:', err);
      setApiError(
        `Unable to connect to live review backend at ${LIVE_API_URL}. Is Ethan's server running? (Run: uvicorn backend.app:app --port 8000). Error: ${err.message}`
      );
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
      {/* Top Header */}
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
            <p className="brand-subtitle">Challenge+X · Unissant UC3 · Team TNUX (Neuro-Symbolic Review Engine)</p>
          </div>
        </div>

        <div className="header-controls">
          <div className="preset-selector-box">
            <label htmlFor="preset-select">Preset Case:</label>
            <select
              id="preset-select"
              value={selectedPresetId}
              onChange={(e) => handlePresetChange(e.target.value)}
              className="select-preset"
            >
              {DEMO_PRESETS.map(p => (
                <option key={p.id} value={p.id}>{p.title}</option>
              ))}
              {selectedPresetId === 'custom_live' && (
                <option value="custom_live">Live Review Result (gpt-oss-20b)</option>
              )}
            </select>
          </div>

          <button
            className={`btn-primary ${showLiveEditor ? 'btn-active' : ''}`}
            onClick={() => setShowLiveEditor(!showLiveEditor)}
            title="Toggle live narrative input editor"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            {showLiveEditor ? 'Close Live Editor' : 'Live Narrative Review'}
          </button>
        </div>
      </header>

      {/* Official Disclaimer Guardrail Banner */}
      <DisclaimerBanner disclaimer={report.disclaimer} />

      {/* Live Narrative Input Drawer / Banner */}
      {showLiveEditor && (
        <section className="live-editor-section">
          <div className="editor-card">
            <div className="editor-header">
              <div className="editor-title">
                <span className="live-pulse-dot"></span>
                <strong>Live Narrative Review Endpoint</strong>
                <code>POST http://localhost:8000/review</code>
              </div>
              <div className="quick-fill-chips">
                <span className="quick-fill-label">Load Template:</span>
                <button
                  type="button"
                  className="quick-fill-btn"
                  onClick={() => setNarrativeInput(Object.values(DEMO_PRESETS[1].data.sentences).join(' '))}
                >
                  Clean Case
                </button>
                <button
                  type="button"
                  className="quick-fill-btn"
                  onClick={() => setNarrativeInput(Object.values(DEMO_PRESETS[0].data.sentences).join(' '))}
                >
                  Gaps Case
                </button>
                <button
                  type="button"
                  className="quick-fill-btn"
                  onClick={() => setNarrativeInput(Object.values(DEMO_PRESETS[2].data.sentences).join(' '))}
                >
                  Contradiction Case
                </button>
                <button
                  type="button"
                  className="quick-fill-btn"
                  onClick={() => setNarrativeInput(Object.values(DEMO_PRESETS[3].data.sentences).join(' '))}
                >
                  Uncovered Charge
                </button>
              </div>
            </div>

            <textarea
              className="live-narrative-textarea"
              rows={5}
              placeholder="Paste or edit an investigative officer narrative here..."
              value={narrativeInput}
              onChange={(e) => setNarrativeInput(e.target.value)}
              disabled={isLoading}
            />

            <div className="editor-actions">
              <span className="live-hint">
                Sends narrative to Ethan's FastAPI endpoint & Unissant's hosted <code>gpt-oss-20b</code> model.
              </span>
              <button
                className="btn-run-review"
                onClick={handleRunLiveReview}
                disabled={isLoading || !narrativeInput.trim()}
              >
                {isLoading ? `Analyzing (${elapsedSeconds}s)...` : '⚡ Run Review (POST /review)'}
              </button>
            </div>
          </div>
        </section>
      )}

      {/* Loading Banner Overlay */}
      {isLoading && (
        <div className="loading-banner" role="status">
          <div className="spinner"></div>
          <div className="loading-text">
            <strong>Running GenAI Fact Extraction & Gap Analysis...</strong>
            <span>Contacting Unissant hosted <code>gpt-oss-20b</code> via Ethan's backend ({elapsedSeconds}s elapsed · typical review 5–15s)</span>
          </div>
        </div>
      )}

      {/* Error Alert Banner */}
      {apiError && (
        <div className="api-error-banner" role="alert">
          <div className="error-icon">⚠️</div>
          <div className="error-body">
            <strong>Live API Connection Notice</strong>
            <p>{apiError}</p>
          </div>
          <button className="btn-dismiss" onClick={() => setApiError(null)}>✕</button>
        </div>
      )}

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
          <span className="metric-label">Human Review Routing</span>
          <span className={`metric-value ${(report.human_review || humanReviewCount > 0) ? 'text-purple' : 'text-slate'}`}>
            {(report.human_review || humanReviewCount > 0) ? (report.multiple_charges ? 'Routed to Human (multi-charge)' : 'Routed to Human') : 'Auto-Resolved'}
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
    </div>
  );
}
