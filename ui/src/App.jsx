import { useState, useEffect } from "react"
import axios from "axios"

const API = "http://localhost:8000"

const GESTURE_LABELS = {
  OPEN_PALM:   "Open Palm",
  FIST:        "Fist",
  POINT_LEFT:  "Point Left",
  POINT_RIGHT: "Point Right",
  THUMBS_UP:   "Thumbs Up",
  PINCH:       "Pinch",
  PEACE:       "Peace ✌️",
}

const ACTION_LABELS = {
  play_pause:     "Play / Pause",
  previous_track: "Previous Track",
  next_track:     "Next Track",
  volume_up:      "Volume Up",
  volume_down:    "Volume Down",
  mute:           "Mute Toggle",
  like_song:      "Like Song",
}

export default function App() {
  const [config, setConfig]       = useState(null)
  const [liveState, setLiveState] = useState({
    raw_gesture: "NONE",
    confirmed_gesture: null,
    hold_progress: 0,
    state_machine: "IDLE"
  })
  const [saved, setSaved]         = useState(false)
  const [mappings, setMappings]   = useState({})
  const [settings, setSettings]   = useState({})

  // Load config on mount
  useEffect(() => {
    axios.get(`${API}/config`).then(res => {
      setConfig(res.data)
      setMappings(res.data.gestures)
      setSettings(res.data.settings)
    })
  }, [])

  // SSE — live gesture stream
  useEffect(() => {
    const es = new EventSource(`${API}/stream`)
    es.onmessage = (e) => {
      const data = JSON.parse(e.data)
      setLiveState(data)
    }
    return () => es.close()
  }, [])

  const handleMappingChange = (gesture, action) => {
    setMappings(prev => ({ ...prev, [gesture]: action }))
    setSaved(false)
  }

  const handleSave = async () => {
    // Save all mappings
    await Promise.all(
      Object.entries(mappings).map(([gesture, action]) =>
        axios.post(`${API}/config/mapping`, { gesture, action })
      )
    )
    // Save settings
    await axios.post(`${API}/config/settings`, {
      hold_frames: settings.hold_frames,
      pinch_threshold: settings.pinch_threshold
    })
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const isActive   = liveState.raw_gesture !== "NONE"
  const isFired    = liveState.confirmed_gesture !== null
  const holdWidth  = `${Math.round(liveState.hold_progress * 100)}%`

  if (!config) return (
    <div style={styles.loading}>connecting to gesture engine...</div>
  )

  return (
    <div style={styles.root}>
      <header style={styles.header}>
        <span style={styles.dot} />
        <h1 style={styles.title}>Air Gesture Media Controller</h1>
        <span style={styles.subtitle}>config panel</span>
      </header>

      {/* Live Monitor */}
      <section style={styles.card}>
        <p style={styles.sectionLabel}>LIVE MONITOR</p>
        <div style={styles.monitor}>
          <div style={{
            ...styles.pulseRing,
            boxShadow: isFired
              ? "0 0 0 4px #00FF9C, 0 0 24px #00FF9C44"
              : isActive
              ? "0 0 0 2px #00FF9C66"
              : "0 0 0 1px #333"
          }}>
            <span style={{
              ...styles.gestureLabel,
              color: isFired ? "#00FF9C" : isActive ? "#aaa" : "#444"
            }}>
              {liveState.raw_gesture}
            </span>
          </div>

          <div style={styles.monitorRight}>
            <div style={styles.progressTrack}>
              <div style={{
                ...styles.progressFill,
                width: holdWidth,
                background: isFired ? "#00FF9C" : "#00FF9C88"
              }} />
            </div>
            <p style={styles.monitorMeta}>
              hold {Math.round(liveState.hold_progress * 100)}%
              &nbsp;·&nbsp;
              <span style={{
                color: liveState.state_machine === "IDLE" ? "#00FF9C" : "#FF6B6B"
              }}>
                {liveState.state_machine}
              </span>
            </p>
            {liveState.confirmed_gesture && (
              <p style={styles.firedLabel}>
                ↳ {ACTION_LABELS[mappings[liveState.confirmed_gesture]] || liveState.confirmed_gesture}
              </p>
            )}
          </div>
        </div>
      </section>

      {/* Gesture Mappings */}
      <section style={styles.card}>
        <p style={styles.sectionLabel}>GESTURE MAPPINGS</p>
        <div style={styles.mappingGrid}>
          {Object.entries(GESTURE_LABELS).map(([gesture, label]) => (
            <div key={gesture} style={{
              ...styles.mappingRow,
              background: liveState.raw_gesture === gesture
                ? "#00FF9C11" : "transparent",
              borderColor: liveState.raw_gesture === gesture
                ? "#00FF9C44" : "#222"
            }}>
              <span style={styles.gestureTag}>{label}</span>
              <span style={styles.arrow}>→</span>
              <select
                style={styles.select}
                value={mappings[gesture] || ""}
                onChange={e => handleMappingChange(gesture, e.target.value)}
              >
                {Object.entries(ACTION_LABELS).map(([action, actionLabel]) => (
                  <option key={action} value={action}>{actionLabel}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
      </section>

      {/* Settings */}
      <section style={styles.card}>
        <p style={styles.sectionLabel}>SETTINGS</p>

        <div style={styles.settingRow}>
          <label style={styles.settingLabel}>
            Hold sensitivity
            <span style={styles.settingValue}>{settings.hold_frames} frames</span>
          </label>
          <input
            type="range" min="3" max="20" step="1"
            value={settings.hold_frames || 8}
            style={styles.slider}
            onChange={e => setSettings(prev => ({
              ...prev, hold_frames: parseInt(e.target.value)
            }))}
          />
          <div style={styles.sliderHints}>
            <span>faster</span><span>slower</span>
          </div>
        </div>

        <div style={styles.settingRow}>
          <label style={styles.settingLabel}>
            Pinch sensitivity
            <span style={styles.settingValue}>
              {(settings.pinch_threshold || 0.28).toFixed(2)}
            </span>
          </label>
          <input
            type="range" min="0.15" max="0.45" step="0.01"
            value={settings.pinch_threshold || 0.28}
            style={styles.slider}
            onChange={e => setSettings(prev => ({
              ...prev, pinch_threshold: parseFloat(e.target.value)
            }))}
          />
          <div style={styles.sliderHints}>
            <span>tighter</span><span>looser</span>
          </div>
        </div>
      </section>

      <div style={styles.saveRow}>
        <button style={{
          ...styles.saveBtn,
          background: saved ? "#00FF9C" : "#fff",
          color: "#000"
        }} onClick={(e) => { e.stopPropagation(); handleSave(); }}>
          {saved ? "Saved ✓" : "Save Changes"}
        </button>
      </div>
    </div>
  )
}

const styles = {
  root: {
    minHeight: "100vh",
    background: "#0A0A0A",
    color: "#fff",
    fontFamily: "'SF Mono', 'Fira Code', monospace",
    padding: "32px 24px",
    maxWidth: "600px",
    margin: "0 auto",
  },
  loading: {
    minHeight: "100vh",
    background: "#0A0A0A",
    color: "#444",
    fontFamily: "monospace",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "14px",
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    marginBottom: "28px",
  },
  dot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    background: "#00FF9C",
    boxShadow: "0 0 8px #00FF9C",
    flexShrink: 0,
  },
  title: {
    margin: 0,
    fontSize: "20px",
    color: "#F8F8F8",
    fontWeight: "600",
    letterSpacing: "0.02em",
  },
  subtitle: {
    fontSize: "10px",
    color: "#a09797",
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    marginLeft: "auto",
  },
  card: {
    background: "#111",
    border: "1px solid #1E1E1E",
    borderRadius: "12px",
    padding: "20px",
    marginBottom: "16px",
  },
  sectionLabel: {
    fontSize: "13px",
    fontWeight: "700",
    color: "#8D8D8D",
    letterSpacing: "0.12em",
    margin: "0 0 16px 0",
  },
  monitor: {
    display: "flex",
    alignItems: "center",
    gap: "24px",
  },
  pulseRing: {
    width: "80px",
    height: "80px",
    borderRadius: "50%",
    border: "none",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    transition: "box-shadow 0.15s ease",
    flexShrink: 0,
    background: "#0A0A0A",
  },
  gestureLabel: {
    fontSize: "9px",
    letterSpacing: "0.06em",
    textAlign: "center",
    transition: "color 0.15s",
    lineHeight: 1.3,
  },
  monitorRight: {
    flex: 1,
  },
  progressTrack: {
    height: "4px",
    background: "#1E1E1E",
    borderRadius: "2px",
    overflow: "hidden",
    marginBottom: "8px",
  },
  progressFill: {
    height: "100%",
    borderRadius: "2px",
    transition: "width 0.05s linear, background 0.15s",
  },
  monitorMeta: {
    fontSize: "12px",
    color: "#555",
    margin: "0 0 4px 0",
  },
  firedLabel: {
    fontSize: "13px",
    color: "#00FF9C",
    margin: 0,
  },
  mappingGrid: {
    display: "flex",
    flexDirection: "column",
    gap: "8px",
  },
  mappingRow: {
    display: "flex",
    alignItems: "center",
    gap: "12px",
    padding: "4px 12px",
    borderRadius: "8px",
    border: "1px solid #222",
    transition: "background 0.15s, border-color 0.15s",
  },
  gestureTag: {
    fontSize: "15px",
    color: "#ccc",
    width: "110px",
    flexShrink: 0,
  },
  arrow: {
    color: "#00FF9C",
    fontSize: "18px",
  },
  select: {
    flex: 1,
    background: "#0A0A0A",
    border: "1px solid #2A2A2A",
    borderRadius: "6px",
    color: "#aaa",
    fontSize: "13px",
    padding: "6px 10px",
    fontFamily: "inherit",
    cursor: "pointer",
    outline: "none",
    appearance: "none",
    WebkitAppearance: "none",
    MozAppearance: "none",
    transition: "all 0.2s ease",
  },
  settingRow: {
    marginBottom: "20px",
  },
  settingLabel: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: "13px",
    color: "#aaa",
    marginBottom: "10px",
  },
  settingValue: {
    color: "#00FF9C",
    fontVariantNumeric: "tabular-nums",
  },
  slider: {
    width: "100%",
    accentColor: "#00FF9C",
    cursor: "pointer",
  },
  sliderHints: {
    display: "flex",
    justifyContent: "space-between",
    fontSize: "10px",
    color: "#6e6c6c",
    marginTop: "4px",
  },
  saveRow: {
    display: "flex",
    justifyContent: "flex-end",
    marginTop: "8px",
  },
  saveBtn: {
    padding: "10px 28px",
    borderRadius: "8px",
    border: "none",
    fontSize: "13px",
    fontFamily: "inherit",
    fontWeight: "600",
    cursor: "pointer",
    transition: "background 0.2s",
    letterSpacing: "0.02em",
  },
}