import { useEffect, useState } from 'react'

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

const shellStyle = {
  minHeight: '100vh',
  background:
    'radial-gradient(circle at top, rgba(31,111,235,0.10), transparent 28%), linear-gradient(180deg, #f7f9fc 0%, #eef3f8 100%)',
  color: '#152033',
}

const pageStyle = {
  width: 'min(1380px, calc(100% - 32px))',
  margin: '0 auto',
  padding: '24px 0 40px',
}

const panelStyle = {
  background: 'rgba(255,255,255,0.88)',
  border: '1px solid rgba(21,32,51,0.10)',
  borderRadius: 18,
  boxShadow: '0 20px 50px rgba(20, 39, 78, 0.08)',
  backdropFilter: 'blur(10px)',
}

const mutedTextStyle = {
  color: '#52607a',
}

function formatLabel(value) {
  if (value === null || value === undefined || value === '') {
    return 'Not available'
  }

  if (typeof value === 'number') {
    return Number.isInteger(value) ? String(value) : value.toFixed(2)
  }

  if (Array.isArray(value)) {
    return value.length ? value.map((item) => formatLabel(item)).join(', ') : 'None'
  }

  if (typeof value === 'object') {
    const preferredKeys = ['title', 'name', 'disease', 'summary', 'message', 'status']

    for (const key of preferredKeys) {
      if (value[key]) {
        return formatLabel(value[key])
      }
    }

    return 'Structured data available'
  }

  return String(value)
}

function toArray(value) {
  return Array.isArray(value) ? value : []
}

function titleCase(value) {
  return String(value || '')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase())
}

function scoreToPercent(score) {
  if (typeof score !== 'number' || Number.isNaN(score)) {
    return 'N/A'
  }

  const normalized = score <= 1 ? score * 100 : score
  return `${Math.round(normalized)}%`
}

function isReadyResponse(data) {
  if (!data) {
    return false
  }

  const status = String(data.status || '').toLowerCase()
  return ['healthy', 'ready', 'success'].includes(status) || Object.keys(data).length > 0
}

function createAssistantIntro(result) {
  const executiveSummary =
    result?.llm_report?.executive_summary ||
    'Analysis is ready. Ask about signals, evidence, risks, or the final recommendation.'

  return {
    role: 'assistant',
    content: executiveSummary,
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

  if (!normalized) {
    return 'Ask about the summary, mechanism, evidence, risks, or top opportunities.'
  }

  if (normalized.includes('summary') || normalized.includes('overview')) {
    return report.executive_summary || formatLabel(summary)
  }

  if (normalized.includes('mechanism') || normalized.includes('target') || normalized.includes('pathway')) {
    const targets = toArray(mechanism.targets)
      .slice(0, 3)
      .map((target) => `${target.name} (${target.action}, ${scoreToPercent(target.confidence)})`)
      .join('; ')

    return [
      `Mechanism class: ${formatLabel(mechanism.mechanism_class)}.`,
      `Primary target: ${formatLabel(mechanism.primary_target)} with ${formatLabel(mechanism.primary_action)}.`,
      targets ? `Top targets: ${targets}.` : '',
      mechanism.pathways?.length ? `Pathways: ${mechanism.pathways.join(', ')}.` : '',
    ]
      .filter(Boolean)
      .join(' ')
  }

  if (
    normalized.includes('top opportunity') ||
    normalized.includes('repurpos') ||
    normalized.includes('opportunit')
  ) {
    if (opportunities.length === 0) {
      return 'No ranked repurposing opportunities were returned in this analysis.'
    }

    return opportunities
      .slice(0, 3)
      .map((item, index) => {
        if (typeof item === 'string') {
          return `${index + 1}. ${item}`
        }

        return `${index + 1}. ${formatLabel(item.disease)} with score ${formatLabel(item.score)} and confidence ${scoreToPercent(item.confidence)}. ${formatLabel(item.rationale)}`
      })
      .join(' ')
  }

  if (normalized.includes('risk') || normalized.includes('warning') || normalized.includes('contra')) {
    const riskItems = toArray(report.risks_and_limitations)
    const contradictionItems = toArray(contradictions.items)
      .slice(0, 3)
      .map((item) => `${formatLabel(item.severity)} severity: ${formatLabel(item.message)}`)

    return [...riskItems.slice(0, 3), ...contradictionItems].join(' ') || 'No explicit risk summary was returned.'
  }

  if (normalized.includes('evidence') || normalized.includes('trial') || normalized.includes('paper')) {
    const trials = toArray(result?.evidence?.clinical_trials)
      .slice(0, 3)
      .map((trial) => `${trial.trial_id}: ${trial.title}`)
    const papers = toArray(result?.evidence?.papers)
      .slice(0, 2)
      .map((paper) => paper.title || paper.citation || JSON.stringify(paper))

    return [...trials, ...papers].join(' ') || 'The evidence layer is sparse for this analysis.'
  }

  if (normalized.includes('recommend')) {
    return report.final_recommendation || 'No final recommendation was generated.'
  }

  return [
    report.executive_summary,
    report.final_recommendation && `Recommendation: ${report.final_recommendation}`,
    toArray(report.key_findings)[0],
  ]
    .filter(Boolean)
    .join(' ')
}

function MetricCard({ label, value }) {
  return (
    <div
      style={{
        padding: 16,
        borderRadius: 14,
        border: '1px solid rgba(21,32,51,0.10)',
        background: '#fff',
      }}
    >
      <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 1.2, color: '#6a7790' }}>
        {label}
      </div>
      <div style={{ marginTop: 10, fontSize: 16, lineHeight: 1.5, color: '#152033' }}>{formatLabel(value)}</div>
    </div>
  )
}

function Pill({ children, tone = 'neutral' }) {
  const tones = {
    neutral: { background: '#eef4fb', color: '#355070' },
    blue: { background: '#e9f2ff', color: '#1f5fbf' },
    green: { background: '#e8f7ef', color: '#177245' },
    amber: { background: '#fff3df', color: '#9a6700' },
    red: { background: '#fdecec', color: '#af3a32' },
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '6px 10px',
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
        ...tones[tone],
      }}
    >
      {children}
    </span>
  )
}

function SectionCard({ title, subtitle, children }) {
  return (
    <section
      style={{
        ...panelStyle,
        padding: 20,
      }}
    >
      <div style={{ marginBottom: 16 }}>
        <div style={{ fontSize: 18, fontWeight: 700 }}>{title}</div>
        {subtitle ? <div style={{ ...mutedTextStyle, marginTop: 6, fontSize: 14 }}>{subtitle}</div> : null}
      </div>
      {children}
    </section>
  )
}

function ListBlock({ items, emptyText }) {
  const safeItems = toArray(items)

  if (safeItems.length === 0) {
    return <div style={{ ...mutedTextStyle, fontSize: 14 }}>{emptyText}</div>
  }

  return (
    <div style={{ display: 'grid', gap: 12 }}>
      {safeItems.map((item, index) => (
        <div
          key={`${index}-${typeof item === 'string' ? item : JSON.stringify(item)}`}
          style={{
            padding: 14,
            borderRadius: 12,
            background: '#fff',
            border: '1px solid rgba(21,32,51,0.08)',
          }}
        >
          {typeof item === 'string' ? (
            <div style={{ lineHeight: 1.6 }}>{item}</div>
          ) : (
            <div style={{ display: 'grid', gap: 8 }}>
              {Object.entries(item).map(([key, value]) => (
                <div key={key} style={{ fontSize: 14, lineHeight: 1.5 }}>
                  <strong>{titleCase(key)}:</strong> {formatLabel(value)}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}

function EvidenceAccordion({ title, items, fallback }) {
  return (
    <div
      style={{
        borderRadius: 14,
        border: '1px solid rgba(21,32,51,0.08)',
        background: '#fff',
        overflow: 'hidden',
      }}
    >
      <div
        style={{
          padding: '12px 14px',
          borderBottom: '1px solid rgba(21,32,51,0.06)',
          fontWeight: 600,
        }}
      >
        {title}
      </div>
      <div style={{ padding: 14 }}>
        <ListBlock items={items} emptyText={fallback} />
      </div>
    </div>
  )
}

function KeyValueRows({ rows }) {
  return (
    <div style={{ display: 'grid', gap: 10 }}>
      {rows
        .filter((row) => row.value !== undefined && row.value !== null && row.value !== '')
        .map((row) => (
          <div
            key={row.label}
            style={{
              display: 'grid',
              gridTemplateColumns: '160px minmax(0, 1fr)',
              gap: 12,
              paddingBottom: 10,
              borderBottom: '1px solid rgba(21,32,51,0.06)',
            }}
          >
            <div style={{ fontSize: 12, textTransform: 'uppercase', letterSpacing: 1, color: '#6a7790' }}>
              {row.label}
            </div>
            <div style={{ fontSize: 14, lineHeight: 1.6 }}>{formatLabel(row.value)}</div>
          </div>
        ))}
    </div>
  )
}

function OpportunityCard({ item, index }) {
  if (typeof item === 'string') {
    return (
      <div style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(21,32,51,0.08)', background: '#fff' }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>Opportunity {index + 1}</div>
        <div style={{ lineHeight: 1.7 }}>{item}</div>
      </div>
    )
  }

  return (
    <div style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(21,32,51,0.08)', background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ fontWeight: 700, fontSize: 18 }}>{formatLabel(item.disease)}</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Pill tone="blue">Score {formatLabel(item.score)}</Pill>
          <Pill tone="green">Confidence {scoreToPercent(item.confidence)}</Pill>
        </div>
      </div>
      <div style={{ marginTop: 12, lineHeight: 1.7 }}>{formatLabel(item.rationale)}</div>
      {toArray(item.signals_used).length ? (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 12 }}>
          {item.signals_used.map((signal) => (
            <Pill key={signal}>{signal}</Pill>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function ContradictionCard({ item }) {
  const toneMap = {
    high: 'red',
    medium: 'amber',
    low: 'blue',
  }

  return (
    <div style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(21,32,51,0.08)', background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div style={{ fontWeight: 700 }}>{formatLabel(item.disease)}</div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Pill tone={toneMap[item.severity] || 'neutral'}>{titleCase(item.severity)}</Pill>
          <Pill>{titleCase(item.type)}</Pill>
        </div>
      </div>
      <div style={{ marginTop: 12, lineHeight: 1.7 }}>{formatLabel(item.message)}</div>
      {toArray(item.affected_domains).length ? (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
          {item.affected_domains.map((domain) => (
            <Pill key={domain}>{titleCase(domain)}</Pill>
          ))}
        </div>
      ) : null}
    </div>
  )
}

function TrialCard({ trial }) {
  return (
    <div style={{ padding: 16, borderRadius: 14, border: '1px solid rgba(21,32,51,0.08)', background: '#fff' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
        <div>
          <div style={{ fontWeight: 700 }}>{formatLabel(trial.title)}</div>
          <div style={{ marginTop: 6, fontSize: 13, color: '#6a7790' }}>{formatLabel(trial.trial_id)}</div>
        </div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Pill tone="blue">{formatLabel(trial.phase)}</Pill>
          <Pill tone="green">{formatLabel(trial.status)}</Pill>
        </div>
      </div>
      <div style={{ marginTop: 12, lineHeight: 1.7 }}>{formatLabel(trial.summary)}</div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 12 }}>
        <Pill>{formatLabel(trial.condition)}</Pill>
        {trial.relevance_score ? <Pill tone="amber">Relevance {formatLabel(trial.relevance_score)}</Pill> : null}
      </div>
    </div>
  )
}

function ReportSection({ title, content }) {
  const items = Array.isArray(content) ? content : null

  return (
    <div style={{ padding: 18, borderRadius: 14, border: '1px solid rgba(21,32,51,0.08)', background: '#fff' }}>
      <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 10 }}>{title}</div>
      {items ? (
        <div style={{ display: 'grid', gap: 10 }}>
          {items.map((item, index) => (
            <div key={`${title}-${index}`} style={{ lineHeight: 1.7 }}>
              {item}
            </div>
          ))}
        </div>
      ) : (
        <div style={{ lineHeight: 1.8 }}>{formatLabel(content)}</div>
      )}
    </div>
  )
}

function App() {
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
        SERVICE_CHECKS.map(async (service) => {
          try {
            const response = await fetch(service.path)
            const text = await response.text()
            let data = {}

            try {
              data = text ? JSON.parse(text) : {}
            } catch {
              data = { raw: text }
            }

            return [
              service.id,
              {
                label: service.label,
                ready: response.ok && isReadyResponse(data),
                status: response.ok ? 'active' : 'inactive',
                detail: data.status || data.service || `${response.status}`,
              },
            ]
          } catch (error) {
            return [
              service.id,
              {
                label: service.label,
                ready: false,
                status: 'inactive',
                detail: error.message,
              },
            ]
          }
        }),
      )

      setServiceHealth(Object.fromEntries(entries))
      setHealthError('')
      setHealthCheckedAt(new Date().toLocaleTimeString())
    } catch (error) {
      setHealthError(error.message)
    }
  }

  useEffect(() => {
    loadHealth()
  }, [])

  useEffect(() => {
    if (!isAnalyzing) {
      return undefined
    }

    const interval = window.setInterval(() => {
      setActiveStage((current) => {
        if (current >= PIPELINE_STAGES.length - 1) {
          return current
        }

        return current + 1
      })
    }, 900)

    return () => window.clearInterval(interval)
  }, [isAnalyzing])

  async function handleAnalyze(event) {
    event.preventDefault()

    if (!molecule.trim()) {
      setAnalysisError('Enter a molecule name to start the orchestration flow.')
      return
    }

    setEntered(true)
    setIsAnalyzing(true)
    setActiveStage(0)
    setAnalysisError('')
    setResult(null)
    setActiveTab('Summary')
    setChatMessages([])

    try {
      const response = await fetch('/api/orchestrator/orchestrate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ molecule: molecule.trim() }),
      })

      const payload = await response.json()

      if (!response.ok) {
        throw new Error(payload.detail || 'Analysis failed.')
      }

      setResult(payload)
      setChatMessages([createAssistantIntro(payload)])
      setActiveStage(PIPELINE_STAGES.length - 1)
    } catch (error) {
      setAnalysisError(error.message)
    } finally {
      setIsAnalyzing(false)
    }
  }

  function handleSendMessage(event) {
    event.preventDefault()

    const message = chatInput.trim()
    if (!message || !result) {
      return
    }

    const userMessage = { role: 'user', content: message }
    const assistantMessage = { role: 'assistant', content: buildChatAnswer(message, result) }

    setChatMessages((current) => [...current, userMessage, assistantMessage])
    setChatInput('')
  }

  const summary = result?.summary || {}
  const mechanism = result?.mechanism_context || {}
  const evidence = result?.evidence || {}
  const intelligence = result?.intelligence || {}
  const contradictions = result?.contradictions || {}
  const report = result?.llm_report || {}
  const agents = result?.agents || {}
  const postCheck = intelligence?.regulatory_postcheck || {}

  return (
    <div style={shellStyle}>
      <style>{`
        * { box-sizing: border-box; }
        button, input, textarea { font: inherit; }
        .fade-in { animation: fadeIn 480ms ease; }
        .pulse-dot { animation: pulse 1.6s infinite; }
        .stage-active { animation: lift 850ms ease infinite alternate; }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes pulse {
          0% { transform: scale(0.95); opacity: 0.55; }
          70% { transform: scale(1.05); opacity: 1; }
          100% { transform: scale(0.95); opacity: 0.55; }
        }
        @keyframes lift {
          from { transform: translateY(0); }
          to { transform: translateY(-4px); }
        }
        @media (max-width: 980px) {
          .top-grid, .results-grid {
            grid-template-columns: 1fr !important;
          }
          .chat-sticky {
            position: static !important;
          }
        }
      `}</style>

      <main style={pageStyle}>
        {!entered ? (
          <section
            className="fade-in"
            style={{
              ...panelStyle,
              minHeight: 'calc(100vh - 64px)',
              display: 'grid',
              placeItems: 'center',
              padding: 32,
            }}
          >
            <div style={{ width: 'min(720px, 100%)', textAlign: 'center' }}>
              <div
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 10,
                  padding: '8px 14px',
                  borderRadius: 999,
                  background: 'rgba(31,111,235,0.08)',
                  color: '#1f4ea8',
                  fontSize: 13,
                  letterSpacing: 0.8,
                  textTransform: 'uppercase',
                }}
              >
                <span
                  className="pulse-dot"
                  style={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    background: '#1f6feb',
                  }}
                />
                Multi-agent decision intelligence
              </div>

              <h1 style={{ margin: '22px 0 12px', fontSize: 'clamp(44px, 9vw, 88px)', lineHeight: 1, letterSpacing: -2.4 }}>
                AgentRx
              </h1>
              <p style={{ ...mutedTextStyle, fontSize: 20, lineHeight: 1.7, margin: '0 auto', maxWidth: 620 }}>
                A transparent interface for molecule analysis, showing how the orchestrator reasons from mechanism to evidence to recommendation.
              </p>

              <div
                style={{
                  marginTop: 28,
                  display: 'flex',
                  justifyContent: 'center',
                  flexWrap: 'wrap',
                  gap: 12,
                }}
              >
                <button
                  type="button"
                  onClick={() => setEntered(true)}
                  style={{
                    border: 'none',
                    borderRadius: 12,
                    padding: '14px 22px',
                    background: '#1f6feb',
                    color: '#fff',
                    fontWeight: 600,
                    cursor: 'pointer',
                    boxShadow: '0 14px 34px rgba(31,111,235,0.22)',
                  }}
                >
                  Enter AgentRx
                </button>
              </div>
            </div>
          </section>
        ) : (
          <div style={{ display: 'grid', gap: 20 }}>
            <section
              className="fade-in"
              style={{
                ...panelStyle,
                padding: 20,
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: 16,
                  flexWrap: 'wrap',
                }}
              >
                <div>
                  <div style={{ fontSize: 13, textTransform: 'uppercase', letterSpacing: 1.4, color: '#5b6a86' }}>
                    AgentRx
                  </div>
                  <div style={{ fontSize: 28, fontWeight: 700, marginTop: 4 }}>Orchestrator Interface</div>
                  <div style={{ ...mutedTextStyle, marginTop: 6, maxWidth: 720 }}>
                    High-level insights first, deeper layers on demand, and a visible pipeline from molecule input to final report.
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => setEntered(false)}
                  style={{
                    borderRadius: 10,
                    border: '1px solid rgba(21,32,51,0.12)',
                    background: '#fff',
                    padding: '10px 14px',
                    cursor: 'pointer',
                  }}
                >
                  Back to landing
                </button>
              </div>
            </section>

            <section
              className="top-grid fade-in"
              style={{
                display: 'grid',
                gridTemplateColumns: '1.3fr 1fr',
                gap: 20,
              }}
            >
              <SectionCard
                title="System Health Dashboard"
                subtitle="Service readiness across the modular backend."
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    gap: 12,
                    flexWrap: 'wrap',
                    marginBottom: 16,
                  }}
                >
                  <div style={{ fontSize: 13, color: '#6a7790' }}>
                    {healthCheckedAt ? `Last checked at ${healthCheckedAt}` : 'Checking services'}
                  </div>
                  <button
                    type="button"
                    onClick={loadHealth}
                    style={{
                      borderRadius: 10,
                      border: '1px solid rgba(21,32,51,0.12)',
                      background: '#fff',
                      padding: '8px 12px',
                      cursor: 'pointer',
                    }}
                  >
                    Refresh health
                  </button>
                </div>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                    gap: 14,
                  }}
                >
                  {SERVICE_CHECKS.map((service) => {
                    const status = serviceHealth[service.id]
                    const ready = status?.ready

                    return (
                      <div
                        key={service.id}
                        style={{
                          padding: 16,
                          borderRadius: 14,
                          border: '1px solid rgba(21,32,51,0.08)',
                          background: '#fff',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12 }}>
                          <div style={{ fontWeight: 600, lineHeight: 1.4 }}>{service.label}</div>
                          <span
                            style={{
                              alignSelf: 'flex-start',
                              padding: '4px 8px',
                              borderRadius: 999,
                              fontSize: 12,
                              background: ready ? 'rgba(17, 152, 89, 0.12)' : 'rgba(219, 74, 57, 0.12)',
                              color: ready ? '#147a4d' : '#b93e31',
                            }}
                          >
                            {ready ? 'active' : 'inactive'}
                          </span>
                        </div>
                        <div style={{ marginTop: 12, ...mutedTextStyle, fontSize: 14 }}>
                          Response readiness: {ready ? 'ready' : 'unavailable'}
                        </div>
                        <div style={{ marginTop: 6, fontSize: 13, color: '#72819a' }}>
                          {status?.detail || 'Checking service...'}
                        </div>
                      </div>
                    )
                  })}
                </div>
                {healthError ? (
                  <div style={{ marginTop: 12, color: '#b93e31', fontSize: 14 }}>{healthError}</div>
                ) : null}
              </SectionCard>

              <SectionCard
                title="Molecule Input"
                subtitle="Trigger the orchestrator with a single molecule query."
              >
                <form onSubmit={handleAnalyze} style={{ display: 'grid', gap: 14 }}>
                  <label style={{ display: 'grid', gap: 8 }}>
                    <span style={{ fontSize: 14, fontWeight: 600 }}>Molecule name</span>
                    <input
                      value={molecule}
                      onChange={(event) => setMolecule(event.target.value)}
                      placeholder="Enter a molecule"
                      style={{
                        width: '100%',
                        borderRadius: 12,
                        border: '1px solid rgba(21,32,51,0.14)',
                        padding: '14px 16px',
                        background: '#fff',
                      }}
                    />
                  </label>
                  <button
                    type="submit"
                    disabled={isAnalyzing}
                    style={{
                      border: 'none',
                      borderRadius: 12,
                      padding: '14px 18px',
                      background: isAnalyzing ? '#8db6f5' : '#1f6feb',
                      color: '#fff',
                      fontWeight: 600,
                      cursor: isAnalyzing ? 'wait' : 'pointer',
                    }}
                  >
                    {isAnalyzing ? 'Analyzing...' : 'Analyze'}
                  </button>
                  {analysisError ? <div style={{ color: '#b93e31', fontSize: 14 }}>{analysisError}</div> : null}
                  {result?.analysis_id ? (
                    <div style={{ ...mutedTextStyle, fontSize: 13 }}>Analysis ID: {result.analysis_id}</div>
                  ) : null}
                </form>
              </SectionCard>
            </section>

            <SectionCard
              title="Execution Visualization"
              subtitle="A minimal live view of the orchestration pipeline as the request runs."
            >
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                  gap: 12,
                }}
              >
                {PIPELINE_STAGES.map((stage, index) => {
                  const completed = !isAnalyzing && result ? true : index < activeStage
                  const active = isAnalyzing && index === activeStage

                  return (
                    <div
                      key={stage}
                      className={active ? 'stage-active' : ''}
                      style={{
                        padding: 14,
                        borderRadius: 14,
                        border: completed || active ? '1px solid rgba(31,111,235,0.32)' : '1px solid rgba(21,32,51,0.08)',
                        background: completed
                          ? 'rgba(31,111,235,0.10)'
                          : active
                            ? 'rgba(31,111,235,0.16)'
                            : '#fff',
                      }}
                    >
                      <div style={{ fontSize: 12, color: '#6a7790', textTransform: 'uppercase', letterSpacing: 1 }}>
                        Stage {index + 1}
                      </div>
                      <div style={{ marginTop: 8, fontWeight: 600, lineHeight: 1.4 }}>{stage}</div>
                      <div style={{ marginTop: 10, fontSize: 13, color: '#52607a' }}>
                        {completed ? 'Completed' : active ? 'Executing' : 'Queued'}
                      </div>
                    </div>
                  )
                })}
              </div>
            </SectionCard>

            {result ? (
              <section
                className="results-grid fade-in"
                style={{
                  display: 'grid',
                  gridTemplateColumns: '360px minmax(0, 1fr)',
                  gap: 20,
                  alignItems: 'start',
                }}
              >
                <div className="chat-sticky" style={{ display: 'grid', gap: 20, position: 'sticky', top: 24 }}>
                  <SectionCard
                    title="Conversational Interface"
                    subtitle="Contextual follow-up over the generated report."
                  >
                    <div
                      style={{
                        display: 'grid',
                        gap: 12,
                        maxHeight: '60vh',
                        overflow: 'auto',
                        paddingRight: 4,
                      }}
                    >
                      {chatMessages.map((message, index) => (
                        <div
                          key={`${message.role}-${index}`}
                          style={{
                            justifySelf: message.role === 'user' ? 'end' : 'start',
                            maxWidth: '92%',
                            padding: '12px 14px',
                            borderRadius: 14,
                            background: message.role === 'user' ? '#1f6feb' : '#f3f6fb',
                            color: message.role === 'user' ? '#fff' : '#152033',
                            lineHeight: 1.6,
                            whiteSpace: 'pre-wrap',
                          }}
                        >
                          {message.content}
                        </div>
                      ))}
                    </div>

                    <form onSubmit={handleSendMessage} style={{ display: 'grid', gap: 10, marginTop: 16 }}>
                      <textarea
                        value={chatInput}
                        onChange={(event) => setChatInput(event.target.value)}
                        placeholder="Ask about evidence, risks, opportunities, or the recommendation"
                        rows={4}
                        style={{
                          width: '100%',
                          resize: 'vertical',
                          borderRadius: 12,
                          border: '1px solid rgba(21,32,51,0.14)',
                          padding: 12,
                          background: '#fff',
                        }}
                      />
                      <button
                        type="submit"
                        style={{
                          border: 'none',
                          borderRadius: 12,
                          padding: '12px 16px',
                          background: '#152033',
                          color: '#fff',
                          fontWeight: 600,
                          cursor: 'pointer',
                        }}
                      >
                        Ask
                      </button>
                    </form>
                  </SectionCard>
                </div>

                <div style={{ display: 'grid', gap: 20 }}>
                  <SectionCard
                    title="Structured Analysis"
                    subtitle="Move from high-level interpretation to raw evidence and conflicts."
                  >
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
                      {TAB_ITEMS.map((tab) => (
                        <button
                          key={tab}
                          type="button"
                          onClick={() => setActiveTab(tab)}
                          style={{
                            borderRadius: 999,
                            border:
                              activeTab === tab
                                ? '1px solid rgba(31,111,235,0.30)'
                                : '1px solid rgba(21,32,51,0.10)',
                            background: activeTab === tab ? 'rgba(31,111,235,0.10)' : '#fff',
                            color: '#152033',
                            padding: '10px 14px',
                            cursor: 'pointer',
                          }}
                        >
                          {tab}
                        </button>
                      ))}
                    </div>
                  </SectionCard>
                  {activeTab === 'Summary' ? (
                    <SectionCard title="Summary" subtitle="First-pass interpretation across all major domains.">
                      <div style={{ display: 'grid', gap: 16 }}>
                        <ReportSection title="Gemini Executive Summary" content={report.executive_summary} />
                        <div
                          style={{
                            display: 'grid',
                            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                            gap: 14,
                          }}
                        >
                        <MetricCard label="Clinical signal" value={summary.clinical_signal} />
                        <MetricCard label="Literature signal" value={summary.literature_signal} />
                        <MetricCard label="Patent status" value={summary.patent_status} />
                        <MetricCard label="Regulatory status" value={summary.regulatory_status} />
                        <MetricCard label="Market signal" value={summary.market_signal} />
                        <MetricCard label="Mechanism signal" value={summary.mechanism_signal} />
                        </div>
                      </div>
                    </SectionCard>
                  ) : null}

                  {activeTab === 'Mechanism Layer' ? (
                    <SectionCard
                      title="Mechanism Layer"
                      subtitle="Pre-agentic reasoning and biological context."
                    >
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                          gap: 14,
                        }}
                      >
                        <MetricCard label="Mechanism of action" value={mechanism.primary_action} />
                        <MetricCard label="Primary target" value={mechanism.primary_target} />
                        <MetricCard label="Mechanism class" value={mechanism.mechanism_class} />
                        <MetricCard label="Confidence" value={scoreToPercent(mechanism.confidence)} />
                        <MetricCard label="Pathways" value={mechanism.pathways} />
                        <MetricCard label="Query terms" value={mechanism.query_terms} />
                      </div>
                      <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
                        {toArray(mechanism.targets).length ? (
                          mechanism.targets.map((target) => (
                            <div
                              key={target.name}
                              style={{
                                padding: 16,
                                borderRadius: 14,
                                border: '1px solid rgba(21,32,51,0.08)',
                                background: '#fff',
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', gap: 12, flexWrap: 'wrap' }}>
                                <div style={{ fontWeight: 700 }}>{target.name}</div>
                                <Pill tone="green">{scoreToPercent(target.confidence)}</Pill>
                              </div>
                              <div style={{ marginTop: 10, lineHeight: 1.6 }}>{formatLabel(target.action)}</div>
                            </div>
                          ))
                        ) : (
                          <div style={{ ...mutedTextStyle }}>No target breakdown returned.</div>
                        )}
                      </div>
                    </SectionCard>
                  ) : null}

                  {activeTab === 'Agents' ? (
                    <SectionCard
                      title="Agent Outputs"
                      subtitle="Consolidated agent highlights instead of raw payloads."
                    >
                      <div style={{ display: 'grid', gap: 14 }}>
                        <ReportSection
                          title="Clinical agent"
                          content={[
                            `Top clinical signal: ${formatLabel(summary.clinical_signal)}`,
                            `${toArray(evidence.clinical_trials).length} trial records retrieved.`,
                            toArray(evidence.clinical_trials)[0]?.title || 'No lead trial highlighted.',
                          ]}
                        />
                        <ReportSection
                          title="Literature agent"
                          content={[
                            `Literature signal: ${formatLabel(summary.literature_signal)}`,
                            `${toArray(evidence.papers).length} paper records retrieved.`,
                            toArray(evidence.papers)[0]?.title || 'No lead literature finding available.',
                          ]}
                        />
                        <ReportSection
                          title="Patent agent"
                          content={[
                            `Patent status: ${formatLabel(summary.patent_status)}`,
                            `${toArray(evidence.patents).length} patent references retrieved.`,
                            agents.patent?.summary || 'No patent summary returned.',
                          ]}
                        />
                        <ReportSection
                          title="Regulatory agent"
                          content={[
                            evidence.regulatory?.regulatory_summary || summary.regulatory_status,
                            `Approved indications: ${formatLabel(evidence.regulatory?.approved_indications)}`,
                            `Contraindications: ${formatLabel(evidence.regulatory?.contradictions)}`,
                          ]}
                        />
                        <ReportSection
                          title="Market agent"
                          content={[
                            `Market signal: ${formatLabel(summary.market_signal)}`,
                            evidence.market?.market_potential
                              ? `Market potential: ${formatLabel(evidence.market.market_potential)}`
                              : 'No market potential summary returned.',
                            evidence.market?.key_statistics?.[0] || 'No lead market statistic available.',
                          ]}
                        />
                      </div>
                    </SectionCard>
                  ) : null}

                  {activeTab === 'Evidence' ? (
                    <SectionCard
                      title="Evidence"
                      subtitle="Consolidated source layer from clinical, literature, patent, regulatory, and market inputs."
                    >
                      <div style={{ display: 'grid', gap: 14 }}>
                        <div style={{ display: 'grid', gap: 12 }}>
                          {toArray(evidence.clinical_trials).slice(0, 6).map((trial) => (
                            <TrialCard key={trial.trial_id || trial.title} trial={trial} />
                          ))}
                          {!toArray(evidence.clinical_trials).length ? (
                            <div style={{ ...mutedTextStyle }}>No clinical trials returned.</div>
                          ) : null}
                        </div>
                        <ReportSection
                          title="Regulatory evidence"
                          content={evidence.regulatory?.regulatory_summary || 'No regulatory evidence returned.'}
                        />
                        <ReportSection
                          title="Market evidence"
                          content={evidence.market?.key_statistics?.slice(0, 3) || 'No market evidence returned.'}
                        />
                      </div>
                    </SectionCard>
                  ) : null}

                  {activeTab === 'Intelligence' ? (
                    <SectionCard
                      title="Intelligence"
                      subtitle="The decision layer where signals are normalized into opportunities."
                    >
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                          gap: 14,
                        }}
                      >
                        <MetricCard label="Confidence score" value={scoreToPercent(intelligence.confidence)} />
                        <MetricCard label="Cross-domain insight" value={intelligence.cross_domain_summary} />
                        <MetricCard label="Signal map" value={intelligence.normalized_signals} />
                        <MetricCard label="Opportunity count" value={toArray(intelligence.top_opportunities).length} />
                      </div>
                      <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
                        {toArray(intelligence.top_opportunities).length ? (
                          intelligence.top_opportunities.map((item, index) => (
                            <OpportunityCard
                              key={typeof item === 'string' ? `${index}-${item}` : item.disease || index}
                              item={item}
                              index={index}
                            />
                          ))
                        ) : toArray(report.top_repurposing_opportunities).length ? (
                          report.top_repurposing_opportunities.map((item, index) => (
                            <OpportunityCard key={`${index}-${item}`} item={item} index={index} />
                          ))
                        ) : (
                          <div style={{ ...mutedTextStyle }}>No top opportunities returned.</div>
                        )}
                      </div>
                    </SectionCard>
                  ) : null}

                  {activeTab === 'Contradictions' ? (
                    <SectionCard
                      title="Contradictions"
                      subtitle="Conflicts, gaps, and regulatory tensions surfaced by the orchestrator."
                    >
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                          gap: 14,
                        }}
                      >
                        <MetricCard label="Total contradictions" value={contradictions.summary?.total} />
                        <MetricCard label="Risk level" value={contradictions.summary?.risk_level} />
                        <MetricCard label="Severity counts" value={contradictions.summary?.severity_counts} />
                      </div>
                      <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
                        {toArray(contradictions.items).length ? (
                          contradictions.items.map((item, index) => (
                            <ContradictionCard key={`${item.type}-${item.disease}-${index}`} item={item} />
                          ))
                        ) : (
                          <div style={{ ...mutedTextStyle }}>No contradictions were returned.</div>
                        )}
                      </div>
                    </SectionCard>
                  ) : null}

                  {activeTab === 'Regulatory Post-check' ? (
                    <SectionCard
                      title="Regulatory Post-check"
                      subtitle="Feasibility validation over approved indications, warnings, and constraint signals."
                    >
                      <div style={{ display: 'grid', gap: 14 }}>
                        <ReportSection
                          title="Approved indications overlap"
                          content={evidence.regulatory?.approved_indications || postCheck.approved_overlap}
                        />
                        <ReportSection
                          title="Warnings and contraindications"
                          content={evidence.regulatory?.contradictions || postCheck.warnings}
                        />
                        <ReportSection
                          title="Adverse events"
                          content={evidence.regulatory?.adverse_events || postCheck.risk_summary}
                        />
                        <ReportSection
                          title="Opportunity-specific checks"
                          content={toArray(postCheck.top_opportunity_risks)}
                        />
                        {!toArray(postCheck.top_opportunity_risks).length &&
                        !toArray(evidence.regulatory?.contradictions).length ? (
                          <div style={{ ...mutedTextStyle }}>No dedicated regulatory post-check payload was returned.</div>
                        ) : null}
                      </div>
                    </SectionCard>
                  ) : null}

                  {activeTab === 'Report' ? (
                    <SectionCard
                      title="Report"
                      subtitle="Presentation-ready output synthesized from the orchestration pipeline."
                    >
                      <div style={{ display: 'grid', gap: 14 }}>
                        <ReportSection title="Executive summary" content={report.executive_summary} />
                        <ReportSection title="Key findings" content={report.key_findings} />
                        <ReportSection title="Top opportunities" content={report.top_repurposing_opportunities} />
                        <ReportSection title="Risks and limitations" content={report.risks_and_limitations} />
                        <ReportSection title="Final recommendation" content={report.final_recommendation} />
                      </div>
                    </SectionCard>
                  ) : null}
                </div>
              </section>
            ) : null}
          </div>
        )}
      </main>
    </div>
  )
}

export default App
