import { useEffect, useRef, useState } from 'react'

/* ─── Constants ─────────────────────────────────────────── */

const PIPELINE_STAGES = [
  'Input',
  'Clinical',
  'Literature',
  'Patent',
  'Regulatory',
  'Market',
  'Aggregation',
  'Intelligence',
  'Regulatory Post-check',
  'Report Generation',
]

const SERVICE_CHECKS = [
  { id: 'orchestrator', label: 'Orchestrator service', path: '/api/orchestrator/docs' },
  { id: 'clinical', label: 'Clinical agent', path: '/api/clinical/health' },
  { id: 'literature', label: 'Literature agent', path: '/api/literature/' },
  { id: 'patent', label: 'Patent agent', path: '/api/patent/health' },
  { id: 'regulatory', label: 'Regulatory agent', path: '/api/regulatory/' },
  { id: 'market', label: 'Market agent', path: '/api/market/health' },
]

const TAB_ITEMS = [
  'Summary',
  'Mechanism Layer',
  'Agents',
  'Evidence',
  'Intelligence',
  'Contradictions',
  'Regulatory Post-check',
  'Report',
]

const LANDING_STATS = [
  { value: '10+', label: 'Specialized Agents' },
  { value: '5', label: 'Evidence Domains' },
  { value: 'LLM', label: 'Synthesized Reports' },
  { value: '< 2m', label: 'Analysis Time' },
]

/* ─── Helpers ───────────────────────────────────────────── */

function formatLabel(value) {
  if (value === null || value === undefined || value === '') return 'Not available'
  if (typeof value === 'number') return Number.isInteger(value) ? String(value) : value.toFixed(2)
  if (Array.isArray(value)) return value.length ? value.map((i) => formatLabel(i)).join(', ') : 'None'
  if (typeof value === 'object') {
    for (const key of ['title', 'name', 'disease', 'summary', 'message', 'status']) {
      if (value[key]) return formatLabel(value[key])
    }
    return 'Structured data available'
  }
  return String(value)
}

function toArray(v) { return Array.isArray(v) ? v : [] }

function titleCase(v) {
  return String(v || '').replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}

function scoreToPercent(score) {
  if (typeof score !== 'number' || Number.isNaN(score)) return 'N/A'
  const normalized = score <= 1 ? score * 100 : score
  return `${Math.round(normalized)}%`
}

function isReadyResponse(data) {
  if (!data) return false
  const status = String(data.status || '').toLowerCase()
  return ['healthy', 'ready', 'success'].includes(status) || Object.keys(data).length > 0
}

function createAssistantIntro(result) {
  return {
    role: 'assistant',
    content: result?.llm_report?.executive_summary ||
      'Analysis is ready. Ask about signals, evidence, risks, or the final recommendation.',
  }
}

function buildChatAnswer(question, result) {
  const normalized = question.trim().toLowerCase()
  const report = result?.llm_report || {}
  const summary = result?.summary || {}
  const mechanism = result?.mechanism_context || {}
  const intelligence = result?.intelligence || {}
  const contradictions = result?.contradictions || {}
  const opportunities = toArray(intelligence.top_opportunities || report.top_repurposing_opportunities)

  if (!normalized) return 'Ask about the summary, mechanism, evidence, risks, or top opportunities.'

  if (normalized.includes('summary') || normalized.includes('overview'))
    return report.executive_summary || formatLabel(summary)

  if (normalized.includes('mechanism') || normalized.includes('target') || normalized.includes('pathway')) {
    const targets = toArray(mechanism.targets).slice(0, 3)
      .map((t) => `${t.name} (${t.action}, ${scoreToPercent(t.confidence)})`).join('; ')
    return [
      `Mechanism class: ${formatLabel(mechanism.mechanism_class)}.`,
      `Primary target: ${formatLabel(mechanism.primary_target)} with ${formatLabel(mechanism.primary_action)}.`,
      targets ? `Top targets: ${targets}.` : '',
      mechanism.pathways?.length ? `Pathways: ${mechanism.pathways.join(', ')}.` : '',
    ].filter(Boolean).join(' ')
  }

  if (normalized.includes('top opportunity') || normalized.includes('repurpos') || normalized.includes('opportunit')) {
    if (!opportunities.length) return 'No ranked repurposing opportunities were returned in this analysis.'
    return opportunities.slice(0, 3).map((item, i) =>
      typeof item === 'string'
        ? `${i + 1}. ${item}`
        : `${i + 1}. ${formatLabel(item.disease)} with score ${formatLabel(item.score)} and confidence ${scoreToPercent(item.confidence)}. ${formatLabel(item.rationale)}`
    ).join(' ')
  }

  if (normalized.includes('risk') || normalized.includes('warning') || normalized.includes('contra')) {
    const riskItems = toArray(report.risks_and_limitations)
    const contradictionItems = toArray(contradictions.items).slice(0, 3)
      .map((item) => `${formatLabel(item.severity)} severity: ${formatLabel(item.message)}`)
    return [...riskItems.slice(0, 3), ...contradictionItems].join(' ') || 'No explicit risk summary was returned.'
  }

  if (normalized.includes('evidence') || normalized.includes('trial') || normalized.includes('paper')) {
    const trials = toArray(result?.evidence?.clinical_trials).slice(0, 3)
      .map((t) => `${t.trial_id}: ${t.title}`)
    const papers = toArray(result?.evidence?.papers).slice(0, 2)
      .map((p) => p.paper_title || p.title || p.citation || JSON.stringify(p))
    return [...trials, ...papers].join(' ') || 'The evidence layer is sparse for this analysis.'
  }

  if (normalized.includes('recommend')) return report.final_recommendation || 'No final recommendation was generated.'

  return [
    report.executive_summary,
    report.final_recommendation && `Recommendation: ${report.final_recommendation}`,
    toArray(report.key_findings)[0],
  ].filter(Boolean).join(' ')
}

/* ─── Molecular animation ───────────────────────────────── */

function MoleculeViz() {
  return (
    <div style={{ position: 'relative', width: '100%', maxWidth: 400, aspectRatio: '1 / 1' }}>
      <div className="molecule-float" style={{ width: '100%', height: '100%' }}>
        <svg
          viewBox="0 0 440 440"
          width="100%"
          height="100%"
          xmlns="http://www.w3.org/2000/svg"
        >
          {/* Glow filter */}
          <defs>
            <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="8" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <filter id="softglow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
            <radialGradient id="coreGrad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#fbbf24" stopOpacity="1" />
              <stop offset="60%" stopColor="#ca8a04" stopOpacity="1" />
              <stop offset="100%" stopColor="#92400e" stopOpacity="0.8" />
            </radialGradient>
            <radialGradient id="nodeGrad" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#fde68a" stopOpacity="1" />
              <stop offset="100%" stopColor="#d97706" stopOpacity="1" />
            </radialGradient>
          </defs>

          {/* Outer halo */}
          <circle cx="220" cy="220" r="196" fill="none" stroke="rgba(202,138,4,0.07)" strokeWidth="1" />
          <circle cx="220" cy="220" r="178" fill="none" stroke="rgba(202,138,4,0.04)" strokeWidth="1" />

          {/* Orbit ring 3 — outermost, slow */}
          <g style={{ animation: 'orbit3 22s linear infinite', transformOrigin: '220px 220px' }}>
            <ellipse cx="220" cy="220" rx="190" ry="68"
              fill="none" stroke="rgba(202,138,4,0.14)" strokeWidth="1.2" strokeDasharray="4 6"
              transform="rotate(-28,220,220)" />
            <circle cx="408" cy="220" r="7" fill="url(#nodeGrad)" filter="url(#softglow)" opacity="0.7"
              style={{ animation: 'orbitPulse 3.5s ease-in-out infinite' }} />
            <circle cx="32" cy="220" r="5" fill="rgba(202,138,4,0.6)" opacity="0.5" />
          </g>

          {/* Orbit ring 2 — mid, reverse */}
          <g style={{ animation: 'orbit2 14s linear infinite', transformOrigin: '220px 220px' }}>
            <ellipse cx="220" cy="220" rx="148" ry="54"
              fill="none" stroke="rgba(202,138,4,0.22)" strokeWidth="1.5"
              transform="rotate(42,220,220)" />
            <circle cx="366" cy="220" r="11" fill="url(#nodeGrad)" filter="url(#softglow)"
              style={{ animation: 'orbitPulse 2.8s ease-in-out infinite 0.5s' }} />
            <circle cx="74" cy="220" r="7" fill="rgba(251,191,36,0.7)" opacity="0.75"
              style={{ animation: 'orbitPulse 2.8s ease-in-out infinite 1.4s' }} />
          </g>

          {/* Orbit ring 1 — inner, fast */}
          <g style={{ animation: 'orbit1 8s linear infinite', transformOrigin: '220px 220px' }}>
            <ellipse cx="220" cy="220" rx="95" ry="36"
              fill="none" stroke="rgba(202,138,4,0.32)" strokeWidth="2" />
            <circle cx="315" cy="220" r="14" fill="url(#nodeGrad)" filter="url(#glow)"
              style={{ animation: 'orbitPulse 2.2s ease-in-out infinite' }} />
            <circle cx="125" cy="220" r="9" fill="rgba(202,138,4,0.9)"
              style={{ animation: 'orbitPulse 2.2s ease-in-out infinite 1.1s' }} />
          </g>

          {/* Connecting spokes (static, decorative) */}
          <line x1="220" y1="220" x2="220" y2="80" stroke="rgba(202,138,4,0.08)" strokeWidth="1" />
          <line x1="220" y1="220" x2="340" y2="295" stroke="rgba(202,138,4,0.08)" strokeWidth="1" />
          <line x1="220" y1="220" x2="100" y2="295" stroke="rgba(202,138,4,0.08)" strokeWidth="1" />

          {/* Central core */}
          <circle cx="220" cy="220" r="32" fill="rgba(202,138,4,0.08)" />
          <circle cx="220" cy="220" r="24" fill="url(#coreGrad)" filter="url(#glow)"
            style={{ animation: 'corePulse 3s ease-in-out infinite' }} />
          <circle cx="220" cy="220" r="10" fill="rgba(255,255,255,0.45)" />
        </svg>
      </div>
    </div>
  )
}

/* ─── Shared UI components ──────────────────────────────── */

const PANEL = {
  background: 'rgba(255,255,255,0.80)',
  border: '1px solid rgba(202, 138, 4, 0.16)',
  borderRadius: 20,
  boxShadow: '0 4px 24px rgba(202,138,4,0.05), 0 1px 3px rgba(0,0,0,0.04)',
  backdropFilter: 'blur(14px)',
}

const MUTED = { color: '#78716c' }

function MetricCard({ label, value }) {
  return (
    <div className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28,25,23,0.09)', background: '#fff' }}>
      <div className="font-mono" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 1.3, color: '#6a7790' }}>{label}</div>
      <div style={{ marginTop: 10, fontSize: 15, lineHeight: 1.5, color: '#1c1917', fontWeight: 500 }}>{formatLabel(value)}</div>
    </div>
  )
}

function Pill({ children, tone = 'neutral' }) {
  const tones = {
    neutral: { background: '#f5f5f4', color: '#44403c' },
    blue: { background: '#fef3c7', color: '#a16207' },
    green: { background: '#f0fdf4', color: '#15803d' },
    amber: { background: '#fef08a', color: '#b45309' },
    red: { background: '#fef2f2', color: '#b91c1c' },
  }
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', padding: '5px 10px', borderRadius: 999, fontSize: 12, fontWeight: 600, ...tones[tone] }}>
      {children}
    </span>
  )
}

function SectionCard({ title, subtitle, children, style }) {
  return (
    <section className="card-hover" style={{ ...PANEL, padding: 24, ...style }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 17, fontWeight: 700, letterSpacing: -0.3 }}>{title}</div>
        {subtitle && <div style={{ ...MUTED, marginTop: 5, fontSize: 13 }}>{subtitle}</div>}
      </div>
      {children}
    </section>
  )
}

function ListBlock({ items, emptyText }) {
  const safe = toArray(items)
  if (!safe.length) return <div style={{ ...MUTED, fontSize: 14 }}>{emptyText}</div>
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      {safe.map((item, i) => (
        <div key={i} className="card-hover" style={{ display: 'flex', justifyContent: 'space-between', gap: 10, padding: 14, borderRadius: 12, background: '#fff', border: '1px solid rgba(28,25,23,0.07)' }}>
          {typeof item === 'string'
            ? <div style={{ lineHeight: 1.6 }}>{item}</div>
            : <div style={{ display: 'grid', gap: 7 }}>
              {Object.entries(item).map(([k, v]) => (
                <div key={k} style={{ fontSize: 14, lineHeight: 1.5 }}>
                  <strong>{titleCase(k)}:</strong> {formatLabel(v)}
                </div>
              ))}
            </div>
          }
        </div>
      ))}
    </div>
  )
}

function KeyValueRows({ rows }) {
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      {rows.filter((r) => r.value !== undefined && r.value !== null && r.value !== '').map((r) => (
        <div key={r.label} style={{ display: 'grid', gridTemplateColumns: '160px minmax(0,1fr)', gap: 12, paddingBottom: 10, borderBottom: '1px solid rgba(28,25,23,0.06)' }}>
          <div className="font-mono" style={{ fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, color: '#6a7790' }}>{r.label}</div>
          <div style={{ fontSize: 14, lineHeight: 1.6 }}>{formatLabel(r.value)}</div>
        </div>
      ))}
    </div>
  )
}

function OpportunityCard({ item, index }) {
  if (typeof item === 'string') return (
    <div className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28,25,23,0.08)', background: '#fff' }}>
      <div style={{ fontWeight: 700, marginBottom: 8 }}>Opportunity {index + 1}</div>
      <div style={{ lineHeight: 1.7 }}>{item}</div>
    </div>
  )
  return (
    <div className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28,25,23,0.08)', background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ fontWeight: 700, fontSize: 17 }}>{formatLabel(item.disease)}</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Pill tone="blue">Score {formatLabel(item.score)}</Pill>
          <Pill tone="green">Confidence {scoreToPercent(item.confidence)}</Pill>
        </div>
      </div>
      <div style={{ marginTop: 12, lineHeight: 1.7 }}>{formatLabel(item.rationale)}</div>
      {toArray(item.signals_used).length ? (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7, marginTop: 12 }}>
          {item.signals_used.map((s) => <Pill key={s}>{s}</Pill>)}
        </div>
      ) : null}
    </div>
  )
}

function ContradictionCard({ item }) {
  const toneMap = { high: 'red', medium: 'amber', low: 'blue' }
  return (
    <div className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28,25,23,0.08)', background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ fontWeight: 700 }}>{formatLabel(item.disease)}</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Pill tone={toneMap[item.severity] || 'neutral'}>{titleCase(item.severity)}</Pill>
          <Pill>{titleCase(item.type)}</Pill>
        </div>
      </div>
      <div style={{ marginTop: 12, lineHeight: 1.7 }}>{formatLabel(item.message)}</div>
      {toArray(item.affected_domains).length ? (
        <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginTop: 12 }}>
          {item.affected_domains.map((d) => <Pill key={d}>{titleCase(d)}</Pill>)}
        </div>
      ) : null}
    </div>
  )
}

function TrialCard({ trial }) {
  return (
    <div className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28,25,23,0.08)', background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontWeight: 700 }}>{formatLabel(trial.title)}</div>
          <div className="font-mono" style={{ marginTop: 5, fontSize: 12, color: '#6a7790' }}>{formatLabel(trial.trial_id)}</div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Pill tone="blue">{formatLabel(trial.phase)}</Pill>
          <Pill tone="green">{formatLabel(trial.status)}</Pill>
        </div>
      </div>
      <div style={{ marginTop: 12, lineHeight: 1.7 }}>{formatLabel(trial.summary)}</div>
      <div style={{ display: 'flex', gap: 7, flexWrap: 'wrap', marginTop: 12 }}>
        <Pill>{formatLabel(trial.condition)}</Pill>
        {trial.relevance_score ? <Pill tone="amber">Relevance {formatLabel(trial.relevance_score)}</Pill> : null}
      </div>
    </div>
  )
}

function ReportSection({ title, content }) {
  const items = Array.isArray(content) ? content : null
  return (
    <div className="card-hover" style={{ padding: 18, borderRadius: 14, border: '1px solid rgba(28,25,23,0.08)', background: '#fff' }}>
      <div style={{ fontSize: 15, fontWeight: 700, marginBottom: 10, letterSpacing: -0.2 }}>{title}</div>
      {items
        ? <div style={{ display: 'grid', gap: 10 }}>
          {items.map((item, i) => <div key={i} style={{ lineHeight: 1.7 }}>{item}</div>)}
        </div>
        : <div style={{ lineHeight: 1.8 }}>{formatLabel(content)}</div>
      }
    </div>
  )
}

/* ─── Landing page ──────────────────────────────────────── */

function LandingPage({ onEnter }) {
  return (
    <div
      className="landing-shell"
      style={{
        minHeight: '100vh',
        background: 'var(--land-bg)',
        position: 'relative',
        overflow: 'hidden',
        /* flex column so nav + content stack cleanly */
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {/* Background layers */}
      <div className="landing-mesh" />
      <div className="landing-grain" />
      <div className="orb orb-1" />
      <div className="orb orb-2" />
      <div className="orb orb-3" />

      {/* Top nav — in normal flow, not absolute */}
      <nav style={{
        position: 'relative', zIndex: 10,
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        padding: '18px 48px',
        borderBottom: '1px solid rgba(202,138,4,0.10)',
        backdropFilter: 'blur(12px)',
        flexShrink: 0,
      }}>
        {/* <div style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
          <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ca8a04', boxShadow: '0 0 10px rgba(202,138,4,0.8)' }} />
          <span className="font-mono" style={{ color: 'rgba(245,240,232,0.55)', fontSize: 12, letterSpacing: 2.2, textTransform: 'uppercase' }}>
            AgentRx
          </span>
        </div> */}
        <div style={{ display: 'flex', gap: 32 }}>
          {['Platform', 'Agents', 'Research'].map((item) => (
            <span key={item} style={{ color: 'rgba(245,240,232,0.3)', fontSize: 13, cursor: 'default', letterSpacing: 0.3 }}>
              {item}
            </span>
          ))}
        </div>
      </nav>

      {/* Main content — fills remaining height, centered */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', position: 'relative', zIndex: 1 }}>
        <div
          className="landing-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: '1fr minmax(0, 420px)',
            gap: 40,
            alignItems: 'center',
            width: 'min(1160px, calc(100% - 96px))',
            margin: '0 auto',
            padding: '40px 0 60px',
          }}
        >

          {/* Left — text */}
          <div>
            {/* Tagline */}
            {/* CENTER TAGLINE (GLOBAL CENTER) */}
            <p
              style={{
                fontFamily: 'serif',
                position: 'absolute',
                top: '1%',
                left: '50%',
                transform: 'translateX(-50%)',
                fontSize: 20,
                fontStyle: 'italic',
                color: '#eaeaeaff',
                letterSpacing: 0.8,
                textAlign: 'center',
                opacity: 0.9,
                zIndex: 5,
                pointerEvents: 'none',
              }}
            >
              Because great drugs deserve a second life.
            </p>
            <br />
            <br />




            {/* Title */}
            <h1
              className="font-display land-title"
              style={{
                margin: '0 0 20px',
                fontSize: 'clamp(64px, 9vw, 112px)',
                lineHeight: 0.92,
                letterSpacing: -3,
                color: 'rgba(245,240,232,0.95)',
                fontWeight: 300,
              }}
            >
              Agent
              <span style={{

                fontStyle: 'italic',
                background: 'linear-gradient(135deg, #fbbf24 0%, #ca8a04 50%, #f59e0b 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}>
                Rx
              </span>
            </h1>
            {/* Badge */}
            {/* Badge */}
            <div
              style={{
                marginTop: 6,
                marginBottom: 20,
                paddingLeft: 226, // small indent from "Agent"
              }}
            >
              <span
                className="font-mono"
                style={{
                  fontSize: 13,
                  color: '#d97706',
                  letterSpacing: 1.5,
                  textTransform: 'uppercase',
                  opacity: 0.8,
                }}
              >
                Multi-agent decision intelligence
              </span>
            </div>


            {/* Subtitle */}
            <p
              className="land-sub"
              style={{
                margin: '0 0 40px',
                fontSize: 18,
                lineHeight: 1.75,
                color: 'rgba(245,240,232,0.52)',
                maxWidth: 500,
              }}
            >
              A transparent orchestration interface for molecule analysis{' '}
              from mechanism to evidence, contradiction to recommendation.
            </p>

            {/* Stat row */}
            {/* <div
              className="land-stats"
              style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 12, marginBottom: 44 }}
            >
              {LANDING_STATS.map((s) => (
                <div key={s.label} className="land-stat">
                  <div
                    className="font-display"
                    style={{ fontSize: 28, fontWeight: 600, color: '#f59e0b', lineHeight: 1, marginBottom: 6 }}
                  >
                    {s.value}
                  </div>
                  <div style={{ fontSize: 11, color: 'rgba(245,240,232,0.38)', letterSpacing: 0.5, lineHeight: 1.4 }}>
                    {s.label}
                  </div>
                </div>
              ))}
            </div> */}
            <div
              className="land-stats"
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(4, 1fr)',
                gap: 20,
                marginBottom: 60,
              }}
            >
              {LANDING_STATS.map((s) => (
                <div
                  key={s.label}
                  style={{
                    padding: '22px 18px',
                    borderRadius: 18,
                    background: 'rgba(255,255,255,0.03)',
                    border: '1px solid rgba(245,158,11,0.15)',
                    backdropFilter: 'blur(12px)',
                    boxShadow: '0 8px 30px rgba(0,0,0,0.4)',
                    transition: 'all 0.3s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-6px)';
                    e.currentTarget.style.border = '1px solid rgba(245,158,11,0.4)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.border = '1px solid rgba(245,158,11,0.15)';
                  }}
                >
                  <div
                    className="font-display"
                    style={{
                      fontSize: 34,
                      fontWeight: 700,
                      background: 'linear-gradient(135deg, #fbbf24, #f59e0b)',
                      WebkitBackgroundClip: 'text',
                      WebkitTextFillColor: 'transparent',
                      marginBottom: 8,
                    }}
                  >
                    {s.value}
                  </div>

                  <div
                    style={{
                      fontSize: 12,
                      color: 'rgba(245,240,232,0.55)',
                      letterSpacing: 0.6,
                    }}
                  >
                    {s.label}
                  </div>
                </div>
              ))}
            </div>

            {/* CTAs */}
            <div className="land-actions" style={{ display: 'flex', gap: 14, flexWrap: 'wrap' }}>
              <button className="cta-btn" onClick={onEnter}>
                Launch Orchestrator →
              </button>
              <button className="cta-outline" onClick={onEnter}>
                View System Health
              </button>
            </div>

            {/* Pipeline labels */}
            <div
              className="land-actions"
              style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 36, alignItems: 'center' }}
            >
              <span style={{ fontSize: 11, color: 'rgba(245,240,232,0.25)', letterSpacing: 0.5, marginRight: 4 }}>
                Pipeline:
              </span>
              {PIPELINE_STAGES.slice(1, 7).map((s, i) => (
                <span key={s} style={{
                  padding: '4px 10px',
                  borderRadius: 6,
                  fontSize: 11,
                  background: 'rgba(202,138,4,0.08)',
                  border: '1px solid rgba(202,138,4,0.14)',
                  color: 'rgba(245,240,232,0.35)',
                  letterSpacing: 0.4,
                }}>
                  {s}
                </span>
              ))}
              <span style={{ fontSize: 11, color: 'rgba(245,240,232,0.2)' }}>+{PIPELINE_STAGES.length - 7} more</span>
            </div>
          </div>

          {/* Right — molecule, overflow clipped to prevent filter bleed */}
          <div
            className="land-mol"
            style={{
              display: 'flex',
              justifyContent: 'center',
              alignItems: 'center',
              overflow: 'hidden',
              borderRadius: 20,
              minHeight: 320,
            }}
          >
            <MoleculeViz />
          </div>
        </div>{/* end landing-grid */}
      </div>{/* end flex content wrapper */}

      {/* Scroll indicator */}


      {/* Bottom decorative border */}
      <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 1, background: 'linear-gradient(90deg, transparent, rgba(202,138,4,0.3), transparent)' }} />
    </div >
  )
}

/* ─── Dashboard ─────────────────────────────────────────── */

function Dashboard({ onBack, molecule, setMolecule, serviceHealth, healthCheckedAt, loadHealth, healthError, isAnalyzing, handleAnalyze, analysisError, result, activeStage, activeTab, setActiveTab, chatInput, setChatInput, chatMessages, handleSendMessage }) {
  const summary = result?.summary || {}
  const mechanism = result?.mechanism_context || {}
  const evidence = result?.evidence || {}
  const intelligence = result?.intelligence || {}
  const contradictions = result?.contradictions || {}
  const report = result?.llm_report || {}
  const agents = result?.agents || {}
  const postCheck = intelligence?.regulatory_postcheck || {}

  return (
    <div className="dashboard-bg">
      <style>{`
        * { box-sizing: border-box; }
        button, input, textarea { font: inherit; }
        @keyframes orbit1 { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        @keyframes orbit2 { from{transform:rotate(0deg)} to{transform:rotate(-360deg)} }
        @keyframes orbit3 { from{transform:rotate(0deg)} to{transform:rotate(360deg)} }
        @keyframes orbitPulse { 0%,100%{opacity:.6} 50%{opacity:1} }
        @keyframes corePulse { 0%,100%{opacity:.85} 50%{opacity:1} }
        @keyframes molFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-18px)} }
      `}</style>

      <main style={{ width: 'min(1380px, calc(100% - 32px))', margin: '0 auto', padding: '24px 0 60px' }}>
        <div className="app-enter" style={{ display: 'grid', gap: 20 }}>

          {/* Header */}
          <section style={{ ...PANEL, padding: '18px 24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ca8a04', boxShadow: '0 0 10px rgba(202,138,4,0.6)' }} />
                  <span className="font-mono" style={{ fontSize: 11, color: '#ca8a04', letterSpacing: 2, textTransform: 'uppercase' }}>AgentRx</span>
                </div>
                <div style={{ width: 1, height: 28, background: 'rgba(28,25,23,0.1)' }} />
                <div>
                  <div className="font-display" style={{ fontSize: 26, fontWeight: 600, letterSpacing: -0.8, lineHeight: 1.1 }}>Orchestrator Interface</div>
                  <div style={{ ...MUTED, fontSize: 13, marginTop: 3 }}>
                    High-level insights first — deeper layers on demand.
                  </div>
                </div>
              </div>
              <button className="btn-hover" onClick={onBack} style={{ borderRadius: 10, border: '1px solid rgba(28,25,23,0.12)', background: '#fff', padding: '10px 16px', cursor: 'pointer', fontSize: 13 }}>
                ← Landing
              </button>
            </div>
          </section>

          {/* Health + Input */}
          <div className="top-grid" style={{ display: 'grid', gridTemplateColumns: '1.4fr 1fr', gap: 20 }}>
            <SectionCard title="System Health" subtitle="Service readiness across the modular backend.">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 12, flexWrap: 'wrap', marginBottom: 16 }}>
                <div className="font-mono" style={{ fontSize: 11, color: '#6a7790', letterSpacing: 0.5 }}>
                  {healthCheckedAt ? `Last checked ${healthCheckedAt}` : 'Checking services…'}
                </div>
                <button onClick={loadHealth} className="btn-hover" style={{ borderRadius: 8, border: '1px solid rgba(28,25,23,0.12)', background: '#fff', padding: '7px 12px', cursor: 'pointer', fontSize: 12 }}>
                  Refresh
                </button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(170px, 1fr))', gap: 12 }}>
                {SERVICE_CHECKS.map((svc) => {
                  const st = serviceHealth[svc.id]
                  const ready = st?.ready
                  return (
                    <div key={svc.id} className="card-hover" style={{ padding: 14, borderRadius: 14, border: '1px solid rgba(28,25,23,0.08)', background: '#fff' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 8 }}>
                        <div style={{ fontWeight: 600, fontSize: 13, lineHeight: 1.4 }}>{svc.label}</div>
                        <span style={{ alignSelf: 'flex-start', padding: '3px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, background: ready ? 'rgba(17,152,89,0.12)' : 'rgba(219,74,57,0.12)', color: ready ? '#147a4d' : '#b93e31' }}>
                          {ready ? 'active' : 'inactive'}
                        </span>
                      </div>
                      <div className="font-mono" style={{ marginTop: 10, fontSize: 11, color: '#72819a' }}>
                        {st?.detail || 'Checking…'}
                      </div>
                    </div>
                  )
                })}
              </div>
              {healthError && <div style={{ marginTop: 12, color: '#b93e31', fontSize: 13 }}>{healthError}</div>}
            </SectionCard>

            <SectionCard title="Molecule Input" subtitle="Trigger the orchestrator with a single query.">
              <form onSubmit={handleAnalyze} style={{ display: 'grid', gap: 14 }}>
                <label style={{ display: 'grid', gap: 7 }}>
                  <span style={{ fontSize: 13, fontWeight: 600, color: '#44403c' }}>Molecule name</span>
                  <input
                    value={molecule}
                    onChange={(e) => setMolecule(e.target.value)}
                    placeholder="e.g. Metformin, Aspirin…"
                    style={{ width: '100%', borderRadius: 12, border: '1.5px solid rgba(28,25,23,0.13)', padding: '13px 15px', background: '#fff', fontSize: 15, outline: 'none', transition: 'border-color 0.2s' }}
                    onFocus={(e) => (e.target.style.borderColor = 'rgba(202,138,4,0.5)')}
                    onBlur={(e) => (e.target.style.borderColor = 'rgba(28,25,23,0.13)')}
                  />
                </label>
                <button
                  type="submit"
                  disabled={isAnalyzing}
                  style={{
                    border: 'none', borderRadius: 12, padding: '13px 18px',
                    background: isAnalyzing
                      ? 'linear-gradient(135deg,#a8c4f0,#7fa8e8)'
                      : 'linear-gradient(135deg,#d97706,#a16207)',
                    color: '#fff', fontWeight: 600, fontSize: 15,
                    cursor: isAnalyzing ? 'wait' : 'pointer',
                    boxShadow: isAnalyzing ? 'none' : '0 6px 20px rgba(202,138,4,0.32)',
                    transition: 'all 0.25s ease',
                  }}
                >
                  {isAnalyzing ? '⟳ Analyzing…' : 'Run Analysis →'}
                </button>
                {analysisError && <div style={{ color: '#b93e31', fontSize: 13, padding: '8px 12px', background: '#fef2f2', borderRadius: 8 }}>{analysisError}</div>}
                {result?.analysis_id && (
                  <div className="font-mono" style={{ ...MUTED, fontSize: 11, letterSpacing: 0.5 }}>ID: {result.analysis_id}</div>
                )}
              </form>
            </SectionCard>
          </div>

          {/* Pipeline */}
          <SectionCard title="Execution Pipeline" subtitle="Live orchestration flow as the request runs.">
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 10 }}>
              {PIPELINE_STAGES.map((stage, idx) => {
                const completed = !isAnalyzing && result ? true : idx < activeStage
                const active = isAnalyzing && idx === activeStage
                return (
                  <div
                    key={stage}
                    className={active ? 'stage-active' : ''}
                    style={{
                      padding: 14, borderRadius: 14,
                      border: completed || active ? '1.5px solid rgba(202,138,4,0.35)' : '1px solid rgba(28,25,23,0.07)',
                      background: completed ? 'rgba(202,138,4,0.09)' : active ? 'rgba(202,138,4,0.18)' : '#fff',
                      transition: 'all 0.3s ease',
                    }}
                  >
                    <div className="font-mono" style={{ fontSize: 10, color: '#6a7790', textTransform: 'uppercase', letterSpacing: 1.2 }}>
                      Stage {idx + 1}
                    </div>
                    <div style={{ marginTop: 7, fontWeight: 600, fontSize: 13, lineHeight: 1.4 }}>{stage}</div>
                    <div style={{ marginTop: 8, fontSize: 12, color: completed ? '#a16207' : active ? '#854d0e' : '#78716c', fontWeight: completed || active ? 600 : 400 }}>
                      {completed ? '✓ Done' : active ? '⟳ Running' : 'Queued'}
                    </div>
                  </div>
                )
              })}
            </div>
          </SectionCard>

          {/* Results */}
          {result && (
            <div
              className="results-grid fade-in"
              style={{ display: 'grid', gridTemplateColumns: '340px minmax(0,1fr)', gap: 20, alignItems: 'start' }}
            >
              {/* Chat panel */}
              <div className="chat-sticky" style={{ display: 'grid', gap: 20, position: 'sticky', top: 24 }}>
                <SectionCard title="Ask the Report" subtitle="Contextual follow-up over the generated analysis.">
                  <div style={{ display: 'grid', gap: 10, maxHeight: '58vh', overflow: 'auto', paddingRight: 2 }}>
                    {chatMessages.map((msg, i) => (
                      <div
                        key={i}
                        style={{
                          justifySelf: msg.role === 'user' ? 'end' : 'start',
                          maxWidth: '90%',
                          padding: '11px 14px',
                          borderRadius: msg.role === 'user' ? '14px 14px 4px 14px' : '14px 14px 14px 4px',
                          background: msg.role === 'user' ? 'linear-gradient(135deg,#d97706,#a16207)' : '#f3f6fb',
                          color: msg.role === 'user' ? '#fff' : '#1c1917',
                          lineHeight: 1.6,
                          fontSize: 14,
                          boxShadow: msg.role === 'user' ? '0 4px 12px rgba(202,138,4,0.25)' : 'none',
                        }}
                      >
                        {msg.content}
                      </div>
                    ))}
                  </div>
                  <form onSubmit={handleSendMessage} style={{ display: 'grid', gap: 10, marginTop: 14 }}>
                    <textarea
                      value={chatInput}
                      onChange={(e) => setChatInput(e.target.value)}
                      placeholder="Ask about evidence, risks, opportunities…"
                      rows={3}
                      style={{ width: '100%', resize: 'vertical', borderRadius: 12, border: '1.5px solid rgba(28,25,23,0.12)', padding: 12, background: '#fff', fontSize: 14 }}
                    />
                    <button type="submit" style={{ border: 'none', borderRadius: 12, padding: '12px 16px', background: '#1c1917', color: '#fff', fontWeight: 600, cursor: 'pointer', fontSize: 14 }}>
                      Ask →
                    </button>
                  </form>
                </SectionCard>
              </div>

              {/* Tabs + content */}
              <div style={{ display: 'grid', gap: 16 }}>
                <SectionCard title="Structured Analysis" subtitle="From high-level interpretation to raw evidence and conflicts.">
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                    {TAB_ITEMS.map((tab) => (
                      <button
                        key={tab}
                        className="btn-hover"
                        onClick={() => setActiveTab(tab)}
                        style={{
                          borderRadius: 999, padding: '9px 14px', cursor: 'pointer', fontSize: 13, fontWeight: activeTab === tab ? 600 : 400,
                          border: activeTab === tab ? '1.5px solid rgba(202,138,4,0.4)' : '1px solid rgba(28,25,23,0.09)',
                          background: activeTab === tab ? 'rgba(202,138,4,0.10)' : '#fff',
                          color: activeTab === tab ? '#854d0e' : '#44403c',
                          transition: 'all 0.2s ease',
                        }}
                      >
                        {tab}
                      </button>
                    ))}
                  </div>
                </SectionCard>

                {activeTab === 'Summary' && (
                  <SectionCard title="Summary" subtitle="First-pass interpretation across all major domains.">
                    <div style={{ display: 'grid', gap: 14 }}>
                      <ReportSection title="Executive Summary" content={report.executive_summary} />
                      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(175px, 1fr))', gap: 12 }}>
                        <MetricCard label="Clinical signal" value={summary.clinical_signal} />
                        <MetricCard label="Literature signal" value={summary.literature_signal} />
                        <MetricCard label="Patent status" value={summary.patent_status} />
                        <MetricCard label="Regulatory status" value={summary.regulatory_status} />
                        <MetricCard label="Market signal" value={summary.market_signal} />
                        <MetricCard label="Mechanism signal" value={summary.mechanism_signal} />
                      </div>
                    </div>
                  </SectionCard>
                )}

                {activeTab === 'Mechanism Layer' && (
                  <SectionCard title="Mechanism Layer" subtitle="Pre-agentic reasoning and biological context.">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 12 }}>
                      <MetricCard label="Mechanism of action" value={mechanism.primary_action} />
                      <MetricCard label="Primary target" value={mechanism.primary_target} />
                      <MetricCard label="Mechanism class" value={mechanism.mechanism_class} />
                      <MetricCard label="Confidence" value={scoreToPercent(mechanism.confidence)} />
                      <MetricCard label="Pathways" value={mechanism.pathways} />
                      <MetricCard label="Query terms" value={mechanism.query_terms} />
                    </div>
                    <div style={{ marginTop: 14, display: 'grid', gap: 10 }}>
                      {toArray(mechanism.targets).length
                        ? mechanism.targets.map((t) => (
                          <div key={t.name} className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28,25,23,0.08)', background: '#fff' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                              <div style={{ fontWeight: 700 }}>{t.name}</div>
                              <Pill tone="green">{scoreToPercent(t.confidence)}</Pill>
                            </div>
                            <div style={{ marginTop: 8, lineHeight: 1.6 }}>{formatLabel(t.action)}</div>
                          </div>
                        ))
                        : <div style={MUTED}>No target breakdown returned.</div>
                      }
                    </div>
                  </SectionCard>
                )}

                {activeTab === 'Agents' && (
                  <SectionCard title="Agent Outputs" subtitle="Consolidated agent highlights.">
                    <div style={{ display: 'grid', gap: 12 }}>
                      <ReportSection title="Clinical agent" content={[`Top clinical signal: ${formatLabel(summary.clinical_signal)}`, `${toArray(evidence.clinical_trials).length} trial records retrieved.`, toArray(evidence.clinical_trials)[0]?.title || 'No lead trial highlighted.']} />
                      <ReportSection title="Literature agent" content={[`Literature signal: ${formatLabel(summary.literature_signal)}`, `${toArray(evidence.papers).length} paper records retrieved.`, toArray(evidence.papers)[0]?.paper_title || toArray(evidence.papers)[0]?.title || 'No lead literature finding.']} />
                      <ReportSection title="Patent agent" content={[`Patent status: ${formatLabel(summary.patent_status)}`, `${toArray(evidence.patents).length} patent references retrieved.`, agents.patent?.summary || 'No patent summary returned.']} />
                      <ReportSection title="Regulatory agent" content={[evidence.regulatory?.regulatory_summary || summary.regulatory_status, `Approved indications: ${formatLabel(evidence.regulatory?.approved_indications)}`, `Contraindications: ${formatLabel(evidence.regulatory?.contradictions)}`]} />
                      <ReportSection title="Market agent" content={[`Market signal: ${formatLabel(summary.market_signal)}`, evidence.market?.market_potential ? `Market potential: ${formatLabel(evidence.market.market_potential)}` : 'No market potential returned.', evidence.market?.key_statistics?.[0] || 'No lead market statistic.']} />
                    </div>
                  </SectionCard>
                )}

                {activeTab === 'Evidence' && (
                  <SectionCard title="Evidence" subtitle="Consolidated source layer from all agents.">
                    <div style={{ display: 'grid', gap: 12 }}>
                      {toArray(evidence.clinical_trials).slice(0, 6).map((trial) => (
                        <TrialCard key={trial.trial_id || trial.title} trial={trial} />
                      ))}
                      {!toArray(evidence.clinical_trials).length && <div style={MUTED}>No clinical trials returned.</div>}
                      <ReportSection title="Regulatory evidence" content={evidence.regulatory?.regulatory_summary || 'No regulatory evidence returned.'} />
                      <ReportSection title="Market evidence" content={evidence.market?.key_statistics?.slice(0, 3) || 'No market evidence returned.'} />
                    </div>
                  </SectionCard>
                )}

                {activeTab === 'Intelligence' && (
                  <SectionCard title="Intelligence" subtitle="The decision layer — signals normalized into opportunities.">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 12 }}>
                      <MetricCard label="Confidence score" value={scoreToPercent(intelligence.confidence)} />
                      <MetricCard label="Cross-domain insight" value={intelligence.cross_domain_summary} />
                      <MetricCard label="Signal map" value={intelligence.normalized_signals} />
                      <MetricCard label="Opportunity count" value={toArray(intelligence.top_opportunities).length} />
                    </div>
                    <div style={{ marginTop: 14, display: 'grid', gap: 10 }}>
                      {toArray(intelligence.top_opportunities).length
                        ? intelligence.top_opportunities.map((item, i) => <OpportunityCard key={i} item={item} index={i} />)
                        : toArray(report.top_repurposing_opportunities).length
                          ? report.top_repurposing_opportunities.map((item, i) => <OpportunityCard key={i} item={item} index={i} />)
                          : <div style={MUTED}>No top opportunities returned.</div>
                      }
                    </div>
                  </SectionCard>
                )}

                {activeTab === 'Contradictions' && (
                  <SectionCard title="Contradictions" subtitle="Conflicts, gaps, and regulatory tensions.">
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: 12 }}>
                      <MetricCard label="Total contradictions" value={contradictions.summary?.total} />
                      <MetricCard label="Risk level" value={contradictions.summary?.risk_level} />
                      <MetricCard label="Severity counts" value={contradictions.summary?.severity_counts} />
                    </div>
                    <div style={{ marginTop: 14, display: 'grid', gap: 10 }}>
                      {toArray(contradictions.items).length
                        ? contradictions.items.map((item, i) => <ContradictionCard key={i} item={item} />)
                        : <div style={MUTED}>No contradictions were returned.</div>
                      }
                    </div>
                  </SectionCard>
                )}

                {activeTab === 'Regulatory Post-check' && (
                  <SectionCard title="Regulatory Post-check" subtitle="Feasibility validation over approved indications and constraint signals.">
                    <div style={{ display: 'grid', gap: 12 }}>
                      <ReportSection title="Approved indications overlap" content={evidence.regulatory?.approved_indications || postCheck.approved_overlap} />
                      <ReportSection title="Warnings and contraindications" content={evidence.regulatory?.contradictions || postCheck.warnings} />
                      <ReportSection title="Adverse events" content={evidence.regulatory?.adverse_events || postCheck.risk_summary} />
                      <ReportSection title="Opportunity-specific checks" content={toArray(postCheck.top_opportunity_risks)} />
                      {!toArray(postCheck.top_opportunity_risks).length && !toArray(evidence.regulatory?.contradictions).length && (
                        <div style={MUTED}>No dedicated regulatory post-check payload was returned.</div>
                      )}
                    </div>
                  </SectionCard>
                )}

                {activeTab === 'Report' && (
                  <SectionCard title="Report" subtitle="Presentation-ready output synthesized from the orchestration pipeline.">
                    <div style={{ display: 'grid', gap: 12 }}>
                      <ReportSection title="Executive summary" content={report.executive_summary} />
                      <ReportSection title="Key findings" content={report.key_findings} />
                      <ReportSection title="Top opportunities" content={report.top_repurposing_opportunities} />
                      <ReportSection title="Risks and limitations" content={report.risks_and_limitations} />
                      <ReportSection title="Final recommendation" content={report.final_recommendation} />
                    </div>
                  </SectionCard>
                )}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

/* ─── Root App ──────────────────────────────────────────── */

export default function App() {
  const [entered, setEntered] = useState(false)
  const [molecule, setMolecule] = useState('Metformin')
  const [serviceHealth, setServiceHealth] = useState({})
  const [healthError, setHealthError] = useState('')
  const [healthCheckedAt, setHealthCheckedAt] = useState('')
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [activeStage, setActiveStage] = useState(0)
  const [result, setResult] = useState(null)
  const [analysisError, setAnalysisError] = useState('')
  const [activeTab, setActiveTab] = useState('Summary')
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState([])

  async function loadHealth() {
    try {
      const entries = await Promise.all(
        SERVICE_CHECKS.map(async (svc) => {
          try {
            const res = await fetch(svc.path)
            const text = await res.text()
            let data = {}
            try { data = text ? JSON.parse(text) : {} } catch { data = { raw: text } }
            return [svc.id, { label: svc.label, ready: res.ok && isReadyResponse(data), status: res.ok ? 'active' : 'inactive', detail: data.status || data.service || `${res.status}` }]
          } catch (err) {
            return [svc.id, { label: svc.label, ready: false, status: 'inactive', detail: err.message }]
          }
        })
      )
      setServiceHealth(Object.fromEntries(entries))
      setHealthError('')
      setHealthCheckedAt(new Date().toLocaleTimeString())
    } catch (err) {
      setHealthError(err.message)
    }
  }

  useEffect(() => { loadHealth() }, [])

  useEffect(() => {
    if (!isAnalyzing) return
    const iv = window.setInterval(() => {
      setActiveStage((c) => c >= PIPELINE_STAGES.length - 1 ? c : c + 1)
    }, 900)
    return () => window.clearInterval(iv)
  }, [isAnalyzing])

  async function handleAnalyze(e) {
    e.preventDefault()
    if (!molecule.trim()) { setAnalysisError('Enter a molecule name to start.'); return }
    setEntered(true)
    setIsAnalyzing(true)
    setActiveStage(0)
    setAnalysisError('')
    setResult(null)
    setActiveTab('Summary')
    setChatMessages([])
    try {
      const res = await fetch('/api/orchestrator/orchestrate', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ molecule: molecule.trim() }) })
      const payload = await res.json()
      if (!res.ok) throw new Error(payload.detail || 'Analysis failed.')
      setResult(payload)
      setChatMessages([createAssistantIntro(payload)])
      setActiveStage(PIPELINE_STAGES.length - 1)
    } catch (err) {
      setAnalysisError(err.message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  function handleSendMessage(e) {
    e.preventDefault()
    const msg = chatInput.trim()
    if (!msg || !result) return
    setChatMessages((prev) => [
      ...prev,
      { role: 'user', content: msg },
      { role: 'assistant', content: buildChatAnswer(msg, result) },
    ])
    setChatInput('')
  }

  if (!entered) {
    return <LandingPage onEnter={() => setEntered(true)} />
  }

  return (
    <Dashboard
      onBack={() => setEntered(false)}
      molecule={molecule} setMolecule={setMolecule}
      serviceHealth={serviceHealth} healthCheckedAt={healthCheckedAt}
      loadHealth={loadHealth} healthError={healthError}
      isAnalyzing={isAnalyzing} handleAnalyze={handleAnalyze}
      analysisError={analysisError} result={result}
      activeStage={activeStage} activeTab={activeTab}
      setActiveTab={setActiveTab} chatInput={chatInput}
      setChatInput={setChatInput} chatMessages={chatMessages}
      handleSendMessage={handleSendMessage}
    />
  )
}
// import { useEffect, useState } from 'react'

// const PIPELINE_STAGES = [
//   'Input',
//   'Clinical',
//   'Literature',
//   'Patent',
//   'Regulatory',
//   'Market',
//   'Aggregation',
//   'Intelligence',
//   'Regulatory Post-check',
//   'Report Generation',
// ]

// const SERVICE_CHECKS = [
//   { id: 'orchestrator', label: 'Orchestrator service', path: '/api/orchestrator/docs' },
//   { id: 'clinical', label: 'Clinical agent', path: '/api/clinical/health' },
//   { id: 'literature', label: 'Literature agent', path: '/api/literature/' },
//   { id: 'patent', label: 'Patent agent', path: '/api/patent/health' },
//   { id: 'regulatory', label: 'Regulatory agent', path: '/api/regulatory/' },
//   { id: 'market', label: 'Market agent', path: '/api/market/health' },
// ]

// const TAB_ITEMS = [
//   'Summary',
//   'Mechanism Layer',
//   'Agents',
//   'Evidence',
//   'Intelligence',
//   'Contradictions',
//   'Regulatory Post-check',
//   'Report',
// ]

// const shellStyle = {
//   minHeight: '100vh',
//   background:
//     'radial-gradient(circle at top, rgba(202, 138, 4, 0.12), transparent 35%), linear-gradient(180deg, #ffffff 0%, #fefce8 100%)',
//   color: '#1c1917',
// }

// const pageStyle = {
//   width: 'min(1380px, calc(100% - 32px))',
//   margin: '0 auto',
//   padding: '24px 0 40px',
// }

// const panelStyle = {
//   background: 'rgba(255,255,255,0.75)',
//   border: '1px solid rgba(202, 138, 4, 0.18)',
//   borderRadius: 18,
//   boxShadow: '0 20px 50px rgba(202, 138, 4, 0.06)',
//   backdropFilter: 'blur(12px)',
// }

// const mutedTextStyle = {
//   color: '#78716c',
// }

// function formatLabel(value) {
//   if (value === null || value === undefined || value === '') {
//     return 'Not available'
//   }

//   if (typeof value === 'number') {
//     return Number.isInteger(value) ? String(value) : value.toFixed(2)
//   }

//   if (Array.isArray(value)) {
//     return value.length ? value.map((item) => formatLabel(item)).join(', ') : 'None'
//   }

//   if (typeof value === 'object') {
//     const preferredKeys = ['title', 'name', 'disease', 'summary', 'message', 'status']

//     for (const key of preferredKeys) {
//       if (value[key]) {
//         return formatLabel(value[key])
//       }
//     }

//     return 'Structured data available'
//   }

//   return String(value)
// }

// function toArray(value) {
//   return Array.isArray(value) ? value : []
// }

// function titleCase(value) {
//   return String(value || '')
//     .replace(/_/g, ' ')
//     .replace(/\b\w/g, (char) => char.toUpperCase())
// }

// function scoreToPercent(score) {
//   if (typeof score !== 'number' || Number.isNaN(score)) {
//     return 'N/A'
//   }

//   const normalized = score <= 1 ? score * 100 : score
//   return `${Math.round(normalized)}%`
// }

// function isReadyResponse(data) {
//   if (!data) {
//     return false
//   }

//   const status = String(data.status || '').toLowerCase()
//   return ['healthy', 'ready', 'success'].includes(status) || Object.keys(data).length > 0
// }

// function createAssistantIntro(result) {
//   const executiveSummary =
//     result?.llm_report?.executive_summary ||
//     'Analysis is ready. Ask about signals, evidence, risks, or the final recommendation.'

//   return {
//     role: 'assistant',
//     content: executiveSummary,
//   }
// }

// function buildChatAnswer(question, result) {
//   const normalized = question.trim().toLowerCase()
//   const report = result?.llm_report || {}
//   const summary = result?.summary || {}
//   const mechanism = result?.mechanism_context || {}
//   const intelligence = result?.intelligence || {}
//   const contradictions = result?.contradictions || {}
//   const opportunities = toArray(intelligence.top_opportunities || report.top_repurposing_opportunities)

//   if (!normalized) {
//     return 'Ask about the summary, mechanism, evidence, risks, or top opportunities.'
//   }

//   if (normalized.includes('summary') || normalized.includes('overview')) {
//     return report.executive_summary || formatLabel(summary)
//   }

//   if (normalized.includes('mechanism') || normalized.includes('target') || normalized.includes('pathway')) {
//     const targets = toArray(mechanism.targets)
//       .slice(0, 3)
//       .map((target) => `${target.name} (${target.action}, ${scoreToPercent(target.confidence)})`)
//       .join('; ')

//     return [
//       `Mechanism class: ${formatLabel(mechanism.mechanism_class)}.`,
//       `Primary target: ${formatLabel(mechanism.primary_target)} with ${formatLabel(mechanism.primary_action)}.`,
//       targets ? `Top targets: ${targets}.` : '',
//       mechanism.pathways?.length ? `Pathways: ${mechanism.pathways.join(', ')}.` : '',
//     ]
//       .filter(Boolean)
//       .join(' ')
//   }

//   if (
//     normalized.includes('top opportunity') ||
//     normalized.includes('repurpos') ||
//     normalized.includes('opportunit')
//   ) {
//     if (opportunities.length === 0) {
//       return 'No ranked repurposing opportunities were returned in this analysis.'
//     }

//     return opportunities
//       .slice(0, 3)
//       .map((item, index) => {
//         if (typeof item === 'string') {
//           return `${index + 1}. ${item}`
//         }

//         return `${index + 1}. ${formatLabel(item.disease)} with score ${formatLabel(item.score)} and confidence ${scoreToPercent(item.confidence)}. ${formatLabel(item.rationale)}`
//       })
//       .join(' ')
//   }

//   if (normalized.includes('risk') || normalized.includes('warning') || normalized.includes('contra')) {
//     const riskItems = toArray(report.risks_and_limitations)
//     const contradictionItems = toArray(contradictions.items)
//       .slice(0, 3)
//       .map((item) => `${formatLabel(item.severity)} severity: ${formatLabel(item.message)}`)

//     return [...riskItems.slice(0, 3), ...contradictionItems].join(' ') || 'No explicit risk summary was returned.'
//   }

//   if (normalized.includes('evidence') || normalized.includes('trial') || normalized.includes('paper')) {
//     const trials = toArray(result?.evidence?.clinical_trials)
//       .slice(0, 3)
//       .map((trial) => `${trial.trial_id}: ${trial.title}`)
//     const papers = toArray(result?.evidence?.papers)
//       .slice(0, 2)
//       .map((paper) => paper.paper_title || paper.title || paper.citation || JSON.stringify(paper))

//     return [...trials, ...papers].join(' ') || 'The evidence layer is sparse for this analysis.'
//   }

//   if (normalized.includes('recommend')) {
//     return report.final_recommendation || 'No final recommendation was generated.'
//   }

//   return [
//     report.executive_summary,
//     report.final_recommendation && `Recommendation: ${report.final_recommendation}`,
//     toArray(report.key_findings)[0],
//   ]
//     .filter(Boolean)
//     .join(' ')
// }

// function MetricCard({ label, value }) {
//   return (
//     <div
//       style={{
//         padding: 16,
//         borderRadius: 14,
//         border: '1px solid rgba(28, 25, 23,0.10)',
//         background: '#fff',
//       }}
//     >
//       <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.2, color: '#6a7790' }}>
//         {label}
//       </div>
//       <div style={{ marginTop: 10, fontSize: 16, lineHeight: 1.5, color: '#1c1917' }}>{formatLabel(value)}</div>
//     </div>
//   )
// }

// function Pill({ children, tone = 'neutral' }) {
//   const tones = {
//     neutral: { background: '#f5f5f4', color: '#44403c' },
//     blue: { background: '#fef3c7', color: '#a16207' }, // re-themed to gold
//     green: { background: '#f0fdf4', color: '#15803d' },
//     amber: { background: '#fef08a', color: '#b45309' },
//     red: { background: '#fef2f2', color: '#b91c1c' },
//   }

//   return (
//     <span
//       style={{
//         display: 'inline-flex',
//         alignItems: 'center',
//         padding: '6px 10px',
//         borderRadius: 999,
//         fontSize: 12,
//         fontWeight: 600,
//         ...tones[tone],
//       }}
//     >
//       {children}
//     </span>
//   )
// }

// function SectionCard({ title, subtitle, children }) {
//   return (
//     <section
//       className="card-hover"
//       style={{
//         ...panelStyle,
//         padding: 24,
//       }}
//     >
//       <div style={{ marginBottom: 16 }}>
//         <div style={{ fontSize: 18, fontWeight: 700 }}>{title}</div>
//         {subtitle ? <div style={{ ...mutedTextStyle, marginTop: 6, fontSize: 14 }}>{subtitle}</div> : null}
//       </div>
//       {children}
//     </section>
//   )
// }

// function ListBlock({ items, emptyText }) {
//   const safeItems = toArray(items)

//   if (safeItems.length === 0) {
//     return <div style={{ ...mutedTextStyle, fontSize: 14 }}>{emptyText}</div>
//   }

//   return (
//     <div style={{ display: 'grid', gap: 12 }}>
//       {safeItems.map((item, index) => (
//         <div
//           key={`${index}-${typeof item === 'string' ? item : JSON.stringify(item)}`}
//           className="card-hover"
//           style={{
//             display: 'flex',
//             justifyContent: 'space-between',
//             gap: 10,
//             padding: 14,
//             borderRadius: 12,
//             background: '#fff',
//             border: '1px solid rgba(28, 25, 23,0.08)',
//           }}
//         >
//           {typeof item === 'string' ? (
//             <div style={{ lineHeight: 1.6 }}>{item}</div>
//           ) : (
//             <div style={{ display: 'grid', gap: 8 }}>
//               {Object.entries(item).map(([key, value]) => (
//                 <div key={key} style={{ fontSize: 14, lineHeight: 1.5 }}>
//                   <strong>{titleCase(key)}:</strong> {formatLabel(value)}
//                 </div>
//               ))}
//             </div>
//           )}
//         </div>
//       ))}
//     </div>
//   )
// }

// function EvidenceAccordion({ title, items, fallback }) {
//   return (
//     <div
//       style={{
//         borderRadius: 14,
//         border: '1px solid rgba(28, 25, 23,0.08)',
//         background: '#fff',
//         overflow: 'hidden',
//       }}
//     >
//       <div
//         style={{
//           padding: '12px 14px',
//           borderBottom: '1px solid rgba(28, 25, 23,0.06)',
//           fontWeight: 600,
//         }}
//       >
//         {title}
//       </div>
//       <div style={{ padding: 14 }}>
//         <ListBlock items={items} emptyText={fallback} />
//       </div>
//     </div>
//   )
// }

// function KeyValueRows({ rows }) {
//   return (
//     <div style={{ display: 'grid', gap: 10 }}>
//       {rows
//         .filter((row) => row.value !== undefined && row.value !== null && row.value !== '')
//         .map((row) => (
//           <div
//             key={row.label}
//             style={{
//               display: 'grid',
//               gridTemplateColumns: '160px minmax(0, 1fr)',
//               gap: 12,
//               paddingBottom: 10,
//               borderBottom: '1px solid rgba(28, 25, 23,0.06)',
//             }}
//           >
//             <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 1, color: '#6a7790' }}>
//               {row.label}
//             </div>
//             <div style={{ fontSize: 14, lineHeight: 1.6 }}>{formatLabel(row.value)}</div>
//           </div>
//         ))}
//     </div>
//   )
// }

// function OpportunityCard({ item, index }) {
//   if (typeof item === 'string') {
//     return (
//       <div className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28, 25, 23,0.08)', background: '#fff' }}>
//         <div style={{ fontWeight: 700, marginBottom: 8 }}>Opportunity {index + 1}</div>
//         <div style={{ lineHeight: 1.7 }}>{item}</div>
//       </div>
//     )
//   }

//   return (
//     <div className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28, 25, 23,0.08)', background: '#fff' }}>
//       <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
//         <div style={{ fontWeight: 700, fontSize: 18 }}>{formatLabel(item.disease)}</div>
//         <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
//           <Pill tone="blue">Score {formatLabel(item.score)}</Pill>
//           <Pill tone="green">Confidence {scoreToPercent(item.confidence)}</Pill>
//         </div>
//       </div>
//       <div style={{ marginTop: 12, lineHeight: 1.7 }}>{formatLabel(item.rationale)}</div>
//       {toArray(item.signals_used).length ? (
//         <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
//           {item.signals_used.map((signal) => (
//             <Pill key={signal}>{signal}</Pill>
//           ))}
//         </div>
//       ) : null}
//     </div>
//   )
// }

// function ContradictionCard({ item }) {
//   const toneMap = {
//     high: 'red',
//     medium: 'amber',
//     low: 'blue',
//   }

//   return (
//     <div className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28, 25, 23,0.08)', background: '#fff' }}>
//       <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
//         <div style={{ fontWeight: 700 }}>{formatLabel(item.disease)}</div>
//         <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
//           <Pill tone={toneMap[item.severity] || 'neutral'}>{titleCase(item.severity)}</Pill>
//           <Pill>{titleCase(item.type)}</Pill>
//         </div>
//       </div>
//       <div style={{ marginTop: 12, lineHeight: 1.7 }}>{formatLabel(item.message)}</div>
//       {toArray(item.affected_domains).length ? (
//         <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
//           {item.affected_domains.map((domain) => (
//             <Pill key={domain}>{titleCase(domain)}</Pill>
//           ))}
//         </div>
//       ) : null}
//     </div>
//   )
// }

// function TrialCard({ trial }) {
//   return (
//     <div className="card-hover" style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(28, 25, 23,0.08)', background: '#fff' }}>
//       <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
//         <div>
//           <div style={{ fontWeight: 700 }}>{formatLabel(trial.title)}</div>
//           <div style={{ marginTop: 6, fontSize: 13, color: '#6a7790' }}>{formatLabel(trial.trial_id)}</div>
//         </div>
//         <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
//           <Pill tone="blue">{formatLabel(trial.phase)}</Pill>
//           <Pill tone="green">{formatLabel(trial.status)}</Pill>
//         </div>
//       </div>
//       <div style={{ marginTop: 12, lineHeight: 1.7 }}>{formatLabel(trial.summary)}</div>
//       <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
//         <Pill>{formatLabel(trial.condition)}</Pill>
//         {trial.relevance_score ? <Pill tone="amber">Relevance {formatLabel(trial.relevance_score)}</Pill> : null}
//       </div>
//     </div>
//   )
// }

// function ReportSection({ title, content }) {
//   const items = Array.isArray(content) ? content : null

//   return (
//     <div className="card-hover" style={{ padding: 18, borderRadius: 14, border: '1px solid rgba(28, 25, 23,0.08)', background: '#fff' }}>
//       <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 10 }}>{title}</div>
//       {items ? (
//         <div style={{ display: 'grid', gap: 10 }}>
//           {items.map((item, index) => (
//             <div key={`${title}-${index}`} style={{ lineHeight: 1.7 }}>
//               {item}
//             </div>
//           ))}
//         </div>
//       ) : (
//         <div style={{ lineHeight: 1.8 }}>{formatLabel(content)}</div>
//       )}
//     </div>
//   )
// }

// function App() {
//   const [entered, setEntered] = useState(false)
//   const [molecule, setMolecule] = useState('Metformin')
//   const [serviceHealth, setServiceHealth] = useState({})
//   const [healthError, setHealthError] = useState('')
//   const [healthCheckedAt, setHealthCheckedAt] = useState('')
//   const [isAnalyzing, setIsAnalyzing] = useState(false)
//   const [activeStage, setActiveStage] = useState(0)
//   const [result, setResult] = useState(null)
//   const [analysisError, setAnalysisError] = useState('')
//   const [activeTab, setActiveTab] = useState('Summary')
//   const [chatInput, setChatInput] = useState('')
//   const [chatMessages, setChatMessages] = useState([])

//   async function loadHealth() {
//     try {
//       const entries = await Promise.all(
//         SERVICE_CHECKS.map(async (service) => {
//           try {
//             const response = await fetch(service.path)
//             const text = await response.text()
//             let data = {}

//             try {
//               data = text ? JSON.parse(text) : {}
//             } catch {
//               data = { raw: text }
//             }

//             return [
//               service.id,
//               {
//                 label: service.label,
//                 ready: response.ok && isReadyResponse(data),
//                 status: response.ok ? 'active' : 'inactive',
//                 detail: data.status || data.service || `${response.status}`,
//               },
//             ]
//           } catch (error) {
//             return [
//               service.id,
//               {
//                 label: service.label,
//                 ready: false,
//                 status: 'inactive',
//                 detail: error.message,
//               },
//             ]
//           }
//         }),
//       )

//       setServiceHealth(Object.fromEntries(entries))
//       setHealthError('')
//       setHealthCheckedAt(new Date().toLocaleTimeString())
//     } catch (error) {
//       setHealthError(error.message)
//     }
//   }

//   useEffect(() => {
//     loadHealth()
//   }, [])

//   useEffect(() => {
//     if (!isAnalyzing) {
//       return undefined
//     }

//     const interval = window.setInterval(() => {
//       setActiveStage((current) => {
//         if (current >= PIPELINE_STAGES.length - 1) {
//           return current
//         }

//         return current + 1
//       })
//     }, 900)

//     return () => window.clearInterval(interval)
//   }, [isAnalyzing])

//   async function handleAnalyze(event) {
//     event.preventDefault()

//     if (!molecule.trim()) {
//       setAnalysisError('Enter a molecule name to start the orchestration flow.')
//       return
//     }

//     setEntered(true)
//     setIsAnalyzing(true)
//     setActiveStage(0)
//     setAnalysisError('')
//     setResult(null)
//     setActiveTab('Summary')
//     setChatMessages([])

//     try {
//       const response = await fetch('/api/orchestrator/orchestrate', {
//         method: 'POST',
//         headers: {
//           'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({ molecule: molecule.trim() }),
//       })

//       const payload = await response.json()

//       if (!response.ok) {
//         throw new Error(payload.detail || 'Analysis failed.')
//       }

//       setResult(payload)
//       setChatMessages([createAssistantIntro(payload)])
//       setActiveStage(PIPELINE_STAGES.length - 1)
//     } catch (error) {
//       setAnalysisError(error.message)
//     } finally {
//       setIsAnalyzing(false)
//     }
//   }

//   function handleSendMessage(event) {
//     event.preventDefault()

//     const message = chatInput.trim()
//     if (!message || !result) {
//       return
//     }

//     const userMessage = { role: 'user', content: message }
//     const assistantMessage = { role: 'assistant', content: buildChatAnswer(message, result) }

//     setChatMessages((current) => [...current, userMessage, assistantMessage])
//     setChatInput('')
//   }

//   const summary = result?.summary || {}
//   const mechanism = result?.mechanism_context || {}
//   const evidence = result?.evidence || {}
//   const intelligence = result?.intelligence || {}
//   const contradictions = result?.contradictions || {}
//   const report = result?.llm_report || {}
//   const agents = result?.agents || {}
//   const postCheck = intelligence?.regulatory_postcheck || {}

//   return (
//     <div className={!entered ? 'landing-bg' : ''} style={shellStyle}>
//       <style>{`
//         * { box-sizing: border-box; }
//         button, input, textarea { font: inherit; }
//         .fade-in { animation: fadeIn 480ms ease; }
//         .pulse-dot { animation: pulse 1.6s infinite; }
//         .stage-active { animation: lift 850ms ease infinite alternate; }
//         @keyframes fadeIn {
//           from { opacity: 0; transform: translateY(10px); }
//           to { opacity: 1; transform: translateY(0); }
//         }
//         @keyframes pulse {
//           0% { transform: scale(0.95); opacity: 0.55; }
//           70% { transform: scale(1.05); opacity: 1; }
//           100% { transform: scale(0.95); opacity: 0.55; }
//         }
//         @keyframes lift {
//           from { transform: translateY(0); }
//           to { transform: translateY(-4px); }
//         }
//         @media (max-width: 980px) {
//           .top-grid, .results-grid {
//             grid-template-columns: 1fr !important;
//           }
//           .chat-sticky {
//             position: static !important;
//           }
//         }
//       `}</style>

//       <main style={pageStyle}>
//         {!entered ? (
//           <section
//             className="fade-in stagger-1"
//             style={{
//               ...panelStyle,
//               minHeight: 'calc(100vh - 64px)',
//               display: 'grid',
//               placeItems: 'center',
//               padding: 32,
//             }}
//           >
//             <div style={{ width: 'min(720px, 100%)', textAlign: 'center' }}>
//               <div
//                 style={{
//                   display: 'inline-flex',
//                   alignItems: 'center',
//                   gap: 10,
//                   padding: '8px 14px',
//                   borderRadius: 999,
//                   background: 'rgba(202, 138, 4, 0.12)',
//                   color: '#a16207',
//                   fontSize: 13,
//                   letterSpacing: 0.8,
//                   textTransform: 'uppercase',
//                 }}
//               >
//                 <span
//                   className="pulse-dot"
//                   style={{
//                     width: 8,
//                     height: 8,
//                     borderRadius: '50%',
//                     background: '#ca8a04',
//                   }}
//                 />
//                 Multi-agent decision intelligence
//               </div>

//               <h1 className="stagger-2" style={{ margin: '22px 0 12px', fontSize: 'clamp(44px, 9vw, 88px)', lineHeight: 1, letterSpacing: -2.4 }}>
//                 AgentRx
//               </h1>
//               <p className="stagger-3" style={{ ...mutedTextStyle, fontSize: 20, lineHeight: 1.7, margin: '0 auto', maxWidth: 620 }}>
//                 A transparent interface for molecule analysis, showing how the orchestrator reasons from mechanism to evidence to recommendation.
//               </p>

//               <div
//                 className="stagger-4"
//                 style={{
//                   marginTop: 28,
//                   display: 'flex',
//                   justifyContent: 'center',
//                   flexWrap: 'wrap',
//                   gap: 12,
//                 }}
//               >
//                 <button
//                   className="btn-hover"
//                   type="button"
//                   onClick={() => setEntered(true)}
//                   style={{
//                     border: 'none',
//                     borderRadius: 12,
//                     padding: '14px 22px',
//                     background: 'linear-gradient(135deg, #d97706 0%, #a16207 100%)',
//                     color: '#fff',
//                     fontWeight: 600,
//                     cursor: 'pointer',
//                     boxShadow: '0 14px 34px rgba(202, 138, 4, 0.3)',
//                     transition: 'all 0.2s ease',
//                   }}
//                 >
//                   Enter AgentRx
//                 </button>
//               </div>
//             </div>
//           </section>
//         ) : (
//           <div style={{ display: 'grid', gap: 20 }}>
//             <section
//               className="fade-in"
//               style={{
//                 ...panelStyle,
//                 padding: 20,
//               }}
//             >
//               <div
//                 style={{
//                   display: 'flex',
//                   justifyContent: 'space-between',
//                   alignItems: 'center',
//                   gap: 16,
//                   flexWrap: 'wrap',
//                 }}
//               >
//                 <div>
//                   <div style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: 1.4, color: '#5b6a86' }}>
//                     AgentRx
//                   </div>
//                   <div style={{ fontSize: 28, fontWeight: 700, marginTop: 4 }}>Orchestrator Interface</div>
//                   <div style={{ ...mutedTextStyle, marginTop: 6, maxWidth: 720 }}>
//                     High-level insights first, deeper layers on demand, and a visible pipeline from molecule input to final report.
//                   </div>
//                 </div>
//                 <button
//                   className="btn-hover"
//                   type="button"
//                   onClick={() => setEntered(false)}
//                   style={{
//                     borderRadius: 10,
//                     border: '1px solid rgba(28, 25, 23,0.12)',
//                     background: '#fff',
//                     padding: '10px 14px',
//                     cursor: 'pointer',
//                   }}
//                 >
//                   Back to landing
//                 </button>
//               </div>
//             </section>

//             <section
//               className="top-grid fade-in"
//               style={{
//                 display: 'grid',
//                 gridTemplateColumns: '1.3fr 1fr',
//                 gap: 20,
//               }}
//             >
//               <SectionCard
//                 title="System Health Dashboard"
//                 subtitle="Service readiness across the modular backend."
//               >
//                 <div
//                   style={{
//                     display: 'flex',
//                     justifyContent: 'space-between',
//                     alignItems: 'center',
//                     gap: 12,
//                     flexWrap: 'wrap',
//                     marginBottom: 16,
//                   }}
//                 >
//                   <div style={{ fontSize: 13, color: '#6a7790' }}>
//                     {healthCheckedAt ? `Last checked at ${healthCheckedAt}` : 'Checking services'}
//                   </div>
//                   <button
//                     type="button"
//                     onClick={loadHealth}
//                     style={{
//                       borderRadius: 10,
//                       border: '1px solid rgba(28, 25, 23,0.12)',
//                       background: '#fff',
//                       padding: '8px 12px',
//                       cursor: 'pointer',
//                     }}
//                   >
//                     Refresh health
//                   </button>
//                 </div>
//                 <div
//                   style={{
//                     display: 'grid',
//                     gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
//                     gap: 14,
//                   }}
//                 >
//                   {SERVICE_CHECKS.map((service) => {
//                     const status = serviceHealth[service.id]
//                     const ready = status?.ready

//                     return (
//                       <div
//                         key={service.id}
//                         style={{
//                           padding: 16,
//                           borderRadius: 14,
//                           border: '1px solid rgba(28, 25, 23,0.08)',
//                           background: '#fff',
//                         }}
//                       >
//                         <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
//                           <div style={{ fontWeight: 600, lineHeight: 1.4 }}>{service.label}</div>
//                           <span
//                             style={{
//                               alignSelf: 'flex-start',
//                               padding: '4px 8px',
//                               borderRadius: 999,
//                               fontSize: 12,
//                               background: ready ? 'rgba(17, 152, 89, 0.12)' : 'rgba(219, 74, 57, 0.12)',
//                               color: ready ? '#147a4d' : '#b93e31',
//                             }}
//                           >
//                             {ready ? 'active' : 'inactive'}
//                           </span>
//                         </div>
//                         <div style={{ marginTop: 12, ...mutedTextStyle, fontSize: 14 }}>
//                           Response readiness: {ready ? 'ready' : 'unavailable'}
//                         </div>
//                         <div style={{ marginTop: 6, fontSize: 13, color: '#72819a' }}>
//                           {status?.detail || 'Checking service...'}
//                         </div>
//                       </div>
//                     )
//                   })}
//                 </div>
//                 {healthError ? (
//                   <div style={{ marginTop: 12, color: '#b93e31', fontSize: 14 }}>{healthError}</div>
//                 ) : null}
//               </SectionCard>

//               <SectionCard
//                 title="Molecule Input"
//                 subtitle="Trigger the orchestrator with a single molecule query."
//               >
//                 <form onSubmit={handleAnalyze} style={{ display: 'grid', gap: 14 }}>
//                   <label style={{ display: 'grid', gap: 8 }}>
//                     <span style={{ fontSize: 14, fontWeight: 600 }}>Molecule name</span>
//                     <input
//                       value={molecule}
//                       onChange={(event) => setMolecule(event.target.value)}
//                       placeholder="Enter a molecule"
//                       style={{
//                         width: '100%',
//                         borderRadius: 12,
//                         border: '1px solid rgba(28, 25, 23,0.14)',
//                         padding: '14px 16px',
//                         background: '#fff',
//                       }}
//                     />
//                   </label>
//                   <button
//                     type="submit"
//                     disabled={isAnalyzing}
//                     style={{
//                       border: 'none',
//                       borderRadius: 12,
//                       padding: '14px 18px',
//                       background: isAnalyzing ? '#8db6f5' : '#ca8a04',
//                       color: '#fff',
//                       fontWeight: 600,
//                       cursor: isAnalyzing ? 'wait' : 'pointer',
//                     }}
//                   >
//                     {isAnalyzing ? 'Analyzing...' : 'Analyze'}
//                   </button>
//                   {analysisError ? <div style={{ color: '#b93e31', fontSize: 14 }}>{analysisError}</div> : null}
//                   {result?.analysis_id ? (
//                     <div style={{ ...mutedTextStyle, fontSize: 13 }}>Analysis ID: {result.analysis_id}</div>
//                   ) : null}
//                 </form>
//               </SectionCard>
//             </section>

//             <SectionCard
//               title="Execution Visualization"
//               subtitle="A minimal live view of the orchestration pipeline as the request runs."
//             >
//               <div
//                 style={{
//                   display: 'grid',
//                   gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
//                   gap: 12,
//                 }}
//               >
//                 {PIPELINE_STAGES.map((stage, index) => {
//                   const completed = !isAnalyzing && result ? true : index < activeStage
//                   const active = isAnalyzing && index === activeStage

//                   return (
//                     <div
//                       key={stage}
//                       className={active ? 'stage-active' : ''}
//                       style={{
//                         padding: 14,
//                         borderRadius: 14,
//                         border: completed || active ? '1px solid rgba(202, 138, 4,0.32)' : '1px solid rgba(28, 25, 23,0.08)',
//                         background: completed
//                           ? 'rgba(202, 138, 4,0.10)'
//                           : active
//                             ? 'rgba(202, 138, 4,0.16)'
//                             : '#fff',
//                       }}
//                     >
//                       <div style={{ fontSize: 12, color: '#6a7790', textTransform: 'uppercase', letterSpacing: 1 }}>
//                         Stage {index + 1}
//                       </div>
//                       <div style={{ marginTop: 8, fontWeight: 600, lineHeight: 1.4 }}>{stage}</div>
//                       <div style={{ marginTop: 10, fontSize: 13, color: '#78716c' }}>
//                         {completed ? 'Completed' : active ? 'Executing' : 'Queued'}
//                       </div>
//                     </div>
//                   )
//                 })}
//               </div>
//             </SectionCard>

//             {result ? (
//               <section
//                 className="results-grid fade-in"
//                 style={{
//                   display: 'grid',
//                   gridTemplateColumns: '360px minmax(0, 1fr)',
//                   gap: 20,
//                   alignItems: 'start',
//                 }}
//               >
//                 <div className="chat-sticky" style={{ display: 'grid', gap: 20, position: 'sticky', top: 24 }}>
//                   <SectionCard
//                     title="Conversational Interface"
//                     subtitle="Contextual follow-up over the generated report."
//                   >
//                     <div
//                       style={{
//                         display: 'grid',
//                         gap: 12,
//                         maxHeight: '60vh',
//                         overflow: 'auto',
//                         paddingRight: 4,
//                       }}
//                     >
//                       {chatMessages.map((message, index) => (
//                         <div
//                           key={`${message.role}-${index}`}
//                           style={{
//                             justifySelf: message.role === 'user' ? 'end' : 'start',
//                             maxWidth: '92%',
//                             padding: '12px 14px',
//                             borderRadius: 14,
//                             background: message.role === 'user' ? '#ca8a04' : '#f3f6fb',
//                             color: message.role === 'user' ? '#fff' : '#1c1917',
//                             lineHeight: 1.6,
//                             whiteSpace: 'pre-wrap',
//                           }}
//                         >
//                           {message.content}
//                         </div>
//                       ))}
//                     </div>

//                     <form onSubmit={handleSendMessage} style={{ display: 'grid', gap: 10, marginTop: 16 }}>
//                       <textarea
//                         value={chatInput}
//                         onChange={(event) => setChatInput(event.target.value)}
//                         placeholder="Ask about evidence, risks, opportunities, or the recommendation"
//                         rows={4}
//                         style={{
//                           width: '100%',
//                           resize: 'vertical',
//                           borderRadius: 12,
//                           border: '1px solid rgba(28, 25, 23,0.14)',
//                           padding: 12,
//                           background: '#fff',
//                         }}
//                       />
//                       <button
//                         type="submit"
//                         style={{
//                           border: 'none',
//                           borderRadius: 12,
//                           padding: '12px 16px',
//                           background: '#1c1917',
//                           color: '#fff',
//                           fontWeight: 600,
//                           cursor: 'pointer',
//                         }}
//                       >
//                         Ask
//                       </button>
//                     </form>
//                   </SectionCard>
//                 </div>

//                 <div style={{ display: 'grid', gap: 20 }}>
//                   <SectionCard
//                     title="Structured Analysis"
//                     subtitle="Move from high-level interpretation to raw evidence and conflicts."
//                   >
//                     <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
//                       {TAB_ITEMS.map((tab) => (
//                         <button
//                           className="btn-hover"
//                           key={tab}
//                           type="button"
//                           onClick={() => setActiveTab(tab)}
//                           style={{
//                             borderRadius: 999,
//                             border:
//                               activeTab === tab
//                                 ? '1px solid rgba(202, 138, 4, 0.35)'
//                                 : '1px solid rgba(28, 25, 23, 0.10)',
//                             background: activeTab === tab ? 'rgba(202, 138, 4, 0.10)' : '#fff',
//                             color: activeTab === tab ? '#854d0e' : '#44403c',
//                             padding: '10px 14px',
//                             cursor: 'pointer',
//                             fontWeight: activeTab === tab ? 600 : 400,
//                             transition: 'all 0.2s ease',
//                           }}
//                         >
//                           {tab}
//                         </button>
//                       ))}
//                     </div>
//                   </SectionCard>
//                   {activeTab === 'Summary' ? (
//                     <SectionCard title="Summary" subtitle="First-pass interpretation across all major domains.">
//                       <div style={{ display: 'grid', gap: 16 }}>
//                         <ReportSection title="Gemini Executive Summary" content={report.executive_summary} />
//                         <div
//                           style={{
//                             display: 'grid',
//                             gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
//                             gap: 14,
//                           }}
//                         >
//                         <MetricCard label="Clinical signal" value={summary.clinical_signal} />
//                         <MetricCard label="Literature signal" value={summary.literature_signal} />
//                         <MetricCard label="Patent status" value={summary.patent_status} />
//                         <MetricCard label="Regulatory status" value={summary.regulatory_status} />
//                         <MetricCard label="Market signal" value={summary.market_signal} />
//                         <MetricCard label="Mechanism signal" value={summary.mechanism_signal} />
//                         </div>
//                       </div>
//                     </SectionCard>
//                   ) : null}

//                   {activeTab === 'Mechanism Layer' ? (
//                     <SectionCard
//                       title="Mechanism Layer"
//                       subtitle="Pre-agentic reasoning and biological context."
//                     >
//                       <div
//                         style={{
//                           display: 'grid',
//                           gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
//                           gap: 14,
//                         }}
//                       >
//                         <MetricCard label="Mechanism of action" value={mechanism.primary_action} />
//                         <MetricCard label="Primary target" value={mechanism.primary_target} />
//                         <MetricCard label="Mechanism class" value={mechanism.mechanism_class} />
//                         <MetricCard label="Confidence" value={scoreToPercent(mechanism.confidence)} />
//                         <MetricCard label="Pathways" value={mechanism.pathways} />
//                         <MetricCard label="Query terms" value={mechanism.query_terms} />
//                       </div>
//                       <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
//                         {toArray(mechanism.targets).length ? (
//                           mechanism.targets.map((target) => (
//                             <div
//                               key={target.name}
//                               style={{
//                                 padding: 16,
//                                 borderRadius: 14,
//                                 border: '1px solid rgba(28, 25, 23,0.08)',
//                                 background: '#fff',
//                               }}
//                             >
//                               <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
//                                 <div style={{ fontWeight: 700 }}>{target.name}</div>
//                                 <Pill tone="green">{scoreToPercent(target.confidence)}</Pill>
//                               </div>
//                               <div style={{ marginTop: 10, lineHeight: 1.6 }}>{formatLabel(target.action)}</div>
//                             </div>
//                           ))
//                         ) : (
//                           <div style={{ ...mutedTextStyle }}>No target breakdown returned.</div>
//                         )}
//                       </div>
//                     </SectionCard>
//                   ) : null}

//                   {activeTab === 'Agents' ? (
//                     <SectionCard
//                       title="Agent Outputs"
//                       subtitle="Consolidated agent highlights instead of raw payloads."
//                     >
//                       <div style={{ display: 'grid', gap: 14 }}>
//                         <ReportSection
//                           title="Clinical agent"
//                           content={[
//                             `Top clinical signal: ${formatLabel(summary.clinical_signal)}`,
//                             `${toArray(evidence.clinical_trials).length} trial records retrieved.`,
//                             toArray(evidence.clinical_trials)[0]?.title || 'No lead trial highlighted.',
//                           ]}
//                         />
//                         <ReportSection
//                           title="Literature agent"
//                           content={[
//                             `Literature signal: ${formatLabel(summary.literature_signal)}`,
//                             `${toArray(evidence.papers).length} paper records retrieved.`,
//                             toArray(evidence.papers)[0]?.paper_title || toArray(evidence.papers)[0]?.title || 'No lead literature finding available.',
//                           ]}
//                         />
//                         <ReportSection
//                           title="Patent agent"
//                           content={[
//                             `Patent status: ${formatLabel(summary.patent_status)}`,
//                             `${toArray(evidence.patents).length} patent references retrieved.`,
//                             agents.patent?.summary || 'No patent summary returned.',
//                           ]}
//                         />
//                         <ReportSection
//                           title="Regulatory agent"
//                           content={[
//                             evidence.regulatory?.regulatory_summary || summary.regulatory_status,
//                             `Approved indications: ${formatLabel(evidence.regulatory?.approved_indications)}`,
//                             `Contraindications: ${formatLabel(evidence.regulatory?.contradictions)}`,
//                           ]}
//                         />
//                         <ReportSection
//                           title="Market agent"
//                           content={[
//                             `Market signal: ${formatLabel(summary.market_signal)}`,
//                             evidence.market?.market_potential
//                               ? `Market potential: ${formatLabel(evidence.market.market_potential)}`
//                               : 'No market potential summary returned.',
//                             evidence.market?.key_statistics?.[0] || 'No lead market statistic available.',
//                           ]}
//                         />
//                       </div>
//                     </SectionCard>
//                   ) : null}

//                   {activeTab === 'Evidence' ? (
//                     <SectionCard
//                       title="Evidence"
//                       subtitle="Consolidated source layer from clinical, literature, patent, regulatory, and market inputs."
//                     >
//                       <div style={{ display: 'grid', gap: 14 }}>
//                         <div style={{ display: 'grid', gap: 12 }}>
//                           {toArray(evidence.clinical_trials).slice(0, 6).map((trial) => (
//                             <TrialCard key={trial.trial_id || trial.title} trial={trial} />
//                           ))}
//                           {!toArray(evidence.clinical_trials).length ? (
//                             <div style={{ ...mutedTextStyle }}>No clinical trials returned.</div>
//                           ) : null}
//                         </div>
//                         <ReportSection
//                           title="Regulatory evidence"
//                           content={evidence.regulatory?.regulatory_summary || 'No regulatory evidence returned.'}
//                         />
//                         <ReportSection
//                           title="Market evidence"
//                           content={evidence.market?.key_statistics?.slice(0, 3) || 'No market evidence returned.'}
//                         />
//                       </div>
//                     </SectionCard>
//                   ) : null}

//                   {activeTab === 'Intelligence' ? (
//                     <SectionCard
//                       title="Intelligence"
//                       subtitle="The decision layer where signals are normalized into opportunities."
//                     >
//                       <div
//                         style={{
//                           display: 'grid',
//                           gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
//                           gap: 14,
//                         }}
//                       >
//                         <MetricCard label="Confidence score" value={scoreToPercent(intelligence.confidence)} />
//                         <MetricCard label="Cross-domain insight" value={intelligence.cross_domain_summary} />
//                         <MetricCard label="Signal map" value={intelligence.normalized_signals} />
//                         <MetricCard label="Opportunity count" value={toArray(intelligence.top_opportunities).length} />
//                       </div>
//                       <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
//                         {toArray(intelligence.top_opportunities).length ? (
//                           intelligence.top_opportunities.map((item, index) => (
//                             <OpportunityCard
//                               key={typeof item === 'string' ? `${index}-${item}` : item.disease || index}
//                               item={item}
//                               index={index}
//                             />
//                           ))
//                         ) : toArray(report.top_repurposing_opportunities).length ? (
//                           report.top_repurposing_opportunities.map((item, index) => (
//                             <OpportunityCard key={`${index}-${item}`} item={item} index={index} />
//                           ))
//                         ) : (
//                           <div style={{ ...mutedTextStyle }}>No top opportunities returned.</div>
//                         )}
//                       </div>
//                     </SectionCard>
//                   ) : null}

//                   {activeTab === 'Contradictions' ? (
//                     <SectionCard
//                       title="Contradictions"
//                       subtitle="Conflicts, gaps, and regulatory tensions surfaced by the orchestrator."
//                     >
//                       <div
//                         style={{
//                           display: 'grid',
//                           gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
//                           gap: 14,
//                         }}
//                       >
//                         <MetricCard label="Total contradictions" value={contradictions.summary?.total} />
//                         <MetricCard label="Risk level" value={contradictions.summary?.risk_level} />
//                         <MetricCard label="Severity counts" value={contradictions.summary?.severity_counts} />
//                       </div>
//                       <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
//                         {toArray(contradictions.items).length ? (
//                           contradictions.items.map((item, index) => (
//                             <ContradictionCard key={`${item.type}-${item.disease}-${index}`} item={item} />
//                           ))
//                         ) : (
//                           <div style={{ ...mutedTextStyle }}>No contradictions were returned.</div>
//                         )}
//                       </div>
//                     </SectionCard>
//                   ) : null}

//                   {activeTab === 'Regulatory Post-check' ? (
//                     <SectionCard
//                       title="Regulatory Post-check"
//                       subtitle="Feasibility validation over approved indications, warnings, and constraint signals."
//                     >
//                       <div style={{ display: 'grid', gap: 14 }}>
//                         <ReportSection
//                           title="Approved indications overlap"
//                           content={evidence.regulatory?.approved_indications || postCheck.approved_overlap}
//                         />
//                         <ReportSection
//                           title="Warnings and contraindications"
//                           content={evidence.regulatory?.contradictions || postCheck.warnings}
//                         />
//                         <ReportSection
//                           title="Adverse events"
//                           content={evidence.regulatory?.adverse_events || postCheck.risk_summary}
//                         />
//                         <ReportSection
//                           title="Opportunity-specific checks"
//                           content={toArray(postCheck.top_opportunity_risks)}
//                         />
//                         {!toArray(postCheck.top_opportunity_risks).length &&
//                         !toArray(evidence.regulatory?.contradictions).length ? (
//                           <div style={{ ...mutedTextStyle }}>No dedicated regulatory post-check payload was returned.</div>
//                         ) : null}
//                       </div>
//                     </SectionCard>
//                   ) : null}

//                   {activeTab === 'Report' ? (
//                     <SectionCard
//                       title="Report"
//                       subtitle="Presentation-ready output synthesized from the orchestration pipeline."
//                     >
//                       <div style={{ display: 'grid', gap: 14 }}>
//                         <ReportSection title="Executive summary" content={report.executive_summary} />
//                         <ReportSection title="Key findings" content={report.key_findings} />
//                         <ReportSection title="Top opportunities" content={report.top_repurposing_opportunities} />
//                         <ReportSection title="Risks and limitations" content={report.risks_and_limitations} />
//                         <ReportSection title="Final recommendation" content={report.final_recommendation} />
//                       </div>
//                     </SectionCard>
//                   ) : null}
//                 </div>
//               </section>
//             ) : null}
//           </div>
//         )}
//       </main>
//     </div>
//   )
// }

// export default App
