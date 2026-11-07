import React from 'react';

/**
 * Highlights quotes inside a sentence string.
 */
function HighlightedSentence({ sentenceId, text, activeQuotes = [], isActive }) {
  if (!activeQuotes.length) {
    return <span>{text}</span>;
  }

  // Create segments based on quote occurrences
  let lowerText = text.toLowerCase();
  let matches = [];

  for (const quote of activeQuotes) {
    if (!quote) continue;
    const qLower = quote.toLowerCase().trim();
    let idx = 0;
    while ((idx = lowerText.indexOf(qLower, idx)) !== -1) {
      matches.push({ start: idx, end: idx + qLower.length, quote });
      idx += qLower.length;
    }
  }

  // Sort and deduplicate matches
  matches.sort((a, b) => a.start - b.start);
  let nonOverlapping = [];
  let lastEnd = 0;
  for (const m of matches) {
    if (m.start >= lastEnd) {
      nonOverlapping.push(m);
      lastEnd = m.end;
    }
  }

  if (nonOverlapping.length === 0) {
    return <span>{text}</span>;
  }

  let elements = [];
  let curr = 0;
  nonOverlapping.forEach((m, i) => {
    if (m.start > curr) {
      elements.push(<span key={`pre-${i}`}>{text.substring(curr, m.start)}</span>);
    }
    elements.push(
      <mark key={`mark-${i}`} className="quote-highlight" title={`Extracted quote: "${m.quote}"`}>
        {text.substring(m.start, m.end)}
      </mark>
    );
    curr = m.end;
  });
  if (curr < text.length) {
    elements.push(<span key="tail">{text.substring(curr)}</span>);
  }

  return <>{elements}</>;
}

export default function NarrativeViewer({
  sentences = {},
  activeSentenceIds = [],
  activeQuotes = [],
  onSentenceClick,
  selectedSentenceId
}) {
  const sentenceEntries = Object.entries(sentences);

  return (
    <div className="narrative-viewer-card">
      <div className="card-header">
        <div className="header-title">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
            <polyline points="14 2 14 8 20 8"></polyline>
            <line x1="16" y1="13" x2="8" y2="13"></line>
            <line x1="16" y1="17" x2="8" y2="17"></line>
            <polyline points="10 9 9 9 8 9"></polyline>
          </svg>
          <h3>Officer Investigative Narrative</h3>
        </div>
        <span className="badge-subtle">{sentenceEntries.length} Sentences</span>
      </div>

      <div className="narrative-body">
        {sentenceEntries.length === 0 ? (
          <p className="empty-text">No narrative text provided.</p>
        ) : (
          sentenceEntries.map(([sId, text]) => {
            const isSentenceActive = activeSentenceIds.includes(sId) || selectedSentenceId === sId;
            return (
              <div
                key={sId}
                id={`sentence-${sId}`}
                className={`narrative-sentence-row ${isSentenceActive ? 'sentence-active' : ''}`}
                onClick={() => onSentenceClick && onSentenceClick(sId)}
              >
                <div className="sentence-id-pill" title="Click to focus this sentence">
                  {sId}
                </div>
                <div className="sentence-text">
                  <HighlightedSentence
                    sentenceId={sId}
                    text={text}
                    activeQuotes={isSentenceActive ? activeQuotes : []}
                    isActive={isSentenceActive}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="narrative-footer">
        <span className="legend-item">
          <span className="legend-pill pill-active">S#</span> Linked Sentence
        </span>
        <span className="legend-item">
          <mark className="legend-mark">Highlighted text</mark> Grounded Quote
        </span>
      </div>
    </div>
  );
}
