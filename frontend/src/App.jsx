import { useState } from 'react'
import { Activity, Send, Terminal, AlertCircle, CheckCircle, Shield, ChevronDown, ChevronUp } from 'lucide-react'
import './index.css'

function App() {
  const [formData, setFormData] = useState({
    request_id: `req_${Math.floor(Math.random() * 10000)}`,
    user_id: 'user_123',
    channel: 'web_portal',
    message: '',
    metadata: {
      product_name: '',
      product_version: '',
      region: 'us-east-1'
    }
  })

  const [showMetadata, setShowMetadata] = useState(false)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleMetadataChange = (key, value) => {
    setFormData(prev => ({
      ...prev,
      metadata: {
        ...prev.metadata,
        [key]: value
      }
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setResult(null)
    setError(null)

    // Construct payload ensuring metadata is sent correctly
    // Send timestamp automatically
    const payload = {
      ...formData,
      metadata: {
        ...formData.metadata,
        timestamp: new Date().toISOString()
      }
    }

    try {
      const response = await fetch('/support/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(errorText || 'Failed to submit request');
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <div className="hero">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <Activity size={48} color="#6366f1" />
          <h1>SupportOps Agent</h1>
        </div>
        <p>Intelligent Triage & Diagnostics System</p>
      </div>

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div className="form-group">
              <label>Request ID</label>
              <input
                type="text"
                value={formData.request_id}
                onChange={e => setFormData({ ...formData, request_id: e.target.value })}
                required
              />
            </div>

            <div className="form-group">
              <label>User ID</label>
              <input
                type="text"
                value={formData.user_id}
                onChange={e => setFormData({ ...formData, user_id: e.target.value })}
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label>Channel</label>
            <select
              value={formData.channel}
              onChange={e => setFormData({ ...formData, channel: e.target.value })}
            >
              <option value="web_portal">Web Portal</option>
              <option value="slack">Slack</option>
              <option value="email">Email</option>
              <option value="api">API</option>
            </select>
          </div>

          <div className="form-group">
            <div
              style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer', marginBottom: '0.5rem', userSelect: 'none' }}
              onClick={() => setShowMetadata(!showMetadata)}
            >
              <label style={{ margin: 0, cursor: 'pointer' }}>Metadata (Optional)</label>
              {showMetadata ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>

            {showMetadata && (
              <div style={{ padding: '1rem', background: 'rgba(0,0,0,0.2)', borderRadius: '8px', marginBottom: '1rem', border: '1px solid rgba(255,255,255,0.05)' }}>
                <div className="form-group">
                  <label>Product Name</label>
                  <input
                    type="text"
                    placeholder="e.g. CloudSync"
                    value={formData.metadata.product_name}
                    onChange={e => handleMetadataChange('product_name', e.target.value)}
                  />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label>Version</label>
                    <input
                      type="text"
                      placeholder="v1.0.0"
                      value={formData.metadata.product_version}
                      onChange={e => handleMetadataChange('product_version', e.target.value)}
                    />
                  </div>
                  <div className="form-group" style={{ marginBottom: 0 }}>
                    <label>Region</label>
                    <input
                      type="text"
                      placeholder="us-east-1"
                      value={formData.metadata.region}
                      onChange={e => handleMetadataChange('region', e.target.value)}
                    />
                  </div>
                </div>
              </div>
            )}
          </div>

          <div className="form-group">
            <label>User Message</label>
            <textarea
              rows="4"
              placeholder="Describe your issue..."
              value={formData.message}
              onChange={e => setFormData({ ...formData, message: e.target.value })}
              required
            />
          </div>

          <button type="submit" disabled={loading || !formData.message}>
            {loading ? <div className="loading-spinner"></div> : <><Send size={18} /> Run Triage</>}
          </button>
        </form>

        {error && (
          <div className="result-section" style={{ borderColor: '#ef4444' }}>
            <div className="status-badge status-error"><AlertCircle size={14} style={{ marginRight: 5, verticalAlign: 'middle' }} /> Error</div>
            <p style={{ color: '#f87171' }}>{error}</p>
          </div>
        )}

        {result && (
          <div className="result-section">
            <div className="status-badge status-success">
              <CheckCircle size={14} style={{ marginRight: 5, verticalAlign: 'middle' }} />
              {result.decision?.action || 'Processed'}
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label>Classification</label>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span style={{ background: '#3730a3', padding: '4px 8px', borderRadius: 4, fontSize: '0.8rem' }}>
                  {result.classification?.category || 'Unknown'}
                </span>
                <span style={{ background: '#3730a3', padding: '4px 8px', borderRadius: 4, fontSize: '0.8rem' }}>
                  Avg Severity: {result.classification?.severity || 'N/A'}
                </span>
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label>Recommended Action</label>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#fff' }}>
                <Shield size={16} color="#fbbf24" />
                <span>{result.decision?.recommended_action?.type || 'Review'}</span>
              </div>
            </div>

            <label><Terminal size={14} style={{ marginRight: 5, verticalAlign: 'middle' }} /> Raw Diagnostics</label>
            <pre className="code-block">
              {JSON.stringify(result.diagnostics, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
