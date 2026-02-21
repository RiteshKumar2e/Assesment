import React, { useState } from 'react';

interface GenerationResult {
    code: string;
    iterations: number;
    logs: string[];
    success: boolean;
    prompt?: string;
}

// ─── Preview Engine ───────────────────────────────────────────────────────────

const getTemplateContent = (code: string): string | null => {
    const parts = code.split(/template\s*:/);
    if (parts.length < 2) return null;
    const after = parts[1].trimStart();

    if (after[0] === '`') {
        let i = 1;
        while (i < after.length) {
            if (after[i] === '\\') { i += 2; continue; }
            if (after[i] === '`') break;
            i++;
        }
        return after.slice(1, i);
    }
    if (after[0] === '"' || after[0] === "'") {
        const q = after[0];
        const end = after.indexOf(q, 1);
        return end !== -1 ? after.slice(1, end) : null;
    }
    return null;
};

const getPreviewHTML = (code: string): string => {
    const extracted = getTemplateContent(code);
    if (extracted?.trim()) return extracted;
    if (code.includes('<div') || code.includes('<section')) {
        const s = code.indexOf('<');
        if (s !== -1) return code.slice(s);
    }
    return `<div style="display:flex;align-items:center;justify-content:center;height:100vh;color:#94a3b8;font-family:sans-serif;font-size:13px;letter-spacing:0.08em;">PREVIEW RENDERING...</div>`;
};

const buildSrcDoc = (code: string): string => {
    const body = getPreviewHTML(code);
    return `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.tailwindcss.com"><\/script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
*,*::before,*::after{box-sizing:border-box}
html,body{margin:0;padding:0;min-height:100vh;font-family:'Inter',sans-serif;background:#f8fafc;color:#0f172a;-webkit-font-smoothing:antialiased}
::-webkit-scrollbar{width:4px}::-webkit-scrollbar-track{background:transparent}::-webkit-scrollbar-thumb{background:#e2e8f0;border-radius:99px}
</style>
</head>
<body>${body}</body>
</html>`;
};

// ─── App ───────────────────────────────────────────────────────────────────────

const EXAMPLE_PROMPTS = [
    'A login form with email, password and a "Sign in" button',
    'An analytics dashboard with 4 KPI metric cards',
    'A user profile card with avatar and connect button',
    'A data table showing team members with status badges',
];

const App = () => {
    const [prompt, setPrompt] = useState('');
    const [result, setResult] = useState<GenerationResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [history, setHistory] = useState<GenerationResult[]>([]);
    const [activeTab, setActiveTab] = useState<'code' | 'logs' | 'preview'>('code');

    const handleGenerate = async () => {
        if (!prompt.trim()) return;
        setLoading(true);
        setActiveTab('logs');
        try {
            const res = await fetch('http://localhost:8080/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, prev_code: result?.code }),
            });
            const data: GenerationResult = await res.json();
            const r = { ...data, prompt };
            setResult(r);
            setHistory(prev => [r, ...prev].slice(0, 6));
            setPrompt('');
            setActiveTab(data.success ? 'preview' : 'code');
        } catch (e) {
            console.error(e);
            setActiveTab('code');
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleGenerate();
    };

    const handleExport = () => {
        if (!result?.code) return;
        const blob = new Blob([result.code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = Object.assign(document.createElement('a'), { href: url, download: 'component.ts' });
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    };

    const statusColor = result?.success ? '#16a34a' : result ? '#d97706' : '#94a3b8';
    const statusLabel = result ? (result.success ? 'Verified' : 'Needs review') : 'Idle';

    return (
        <div style={{ minHeight: '100vh', background: '#f8fafc', fontFamily: "'Inter', sans-serif", color: '#0f172a' }}>

            {/* ── Header ── */}
            <header style={{ background: '#ffffff', borderBottom: '1px solid #e2e8f0', position: 'sticky', top: 0, zIndex: 50 }}>
                <div style={{ maxWidth: 1200, margin: '0 auto', padding: '0 24px', height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <div style={{ width: 34, height: 34, borderRadius: 10, background: '#4f46e5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
                            </svg>
                        </div>
                        <div>
                            <span style={{ fontWeight: 700, fontSize: 15, color: '#0f172a', letterSpacing: '-0.02em' }}>Component Architect</span>
                            <span style={{ marginLeft: 8, fontSize: 11, background: '#eef2ff', color: '#4f46e5', padding: '2px 8px', borderRadius: 99, fontWeight: 600, letterSpacing: '0.04em' }}>v2.0</span>
                        </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                        {result && (
                            <button onClick={() => { setResult(null); setHistory([]); setActiveTab('code'); }}
                                style={{ fontSize: 12, fontWeight: 600, color: '#dc2626', background: '#fee2e2', border: 'none', borderRadius: 8, padding: '6px 14px', cursor: 'pointer' }}>
                                Clear
                            </button>
                        )}
                        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: '#64748b', fontWeight: 500 }}>
                            <div style={{ width: 7, height: 7, borderRadius: '50%', background: '#16a34a' }} />
                            System Ready
                        </div>
                    </div>
                </div>
            </header>

            <main style={{ maxWidth: 1200, margin: '0 auto', padding: '40px 24px' }}>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.6fr', gap: 32, alignItems: 'start' }}>

                    {/* ── Left Panel ── */}
                    <div className="left-panel" style={{ display: 'flex', flexDirection: 'column', gap: 20, height: 700, overflowY: 'auto', paddingRight: 4 }}>

                        {/* Hero text */}
                        <div>
                            <h1 style={{ fontSize: 32, fontWeight: 900, letterSpacing: '-0.04em', color: '#0f172a', margin: 0, lineHeight: 1.1 }}>
                                {result ? 'Refine your\ncomponent.' : 'Build Angular\ncomponents.'}
                            </h1>
                            <p style={{ marginTop: 10, fontSize: 14, color: '#64748b', lineHeight: 1.7 }}>
                                Describe what you need in plain English. The AI pipeline generates, validates, and self-corrects production-ready Angular code.
                            </p>
                        </div>

                        {/* Prompt box */}
                        <div style={{ background: '#ffffff', border: '1.5px solid #e2e8f0', borderRadius: 16, overflow: 'hidden', boxShadow: '0 2px 12px rgba(15,23,42,0.06)' }}>
                            <textarea
                                value={prompt}
                                onChange={e => setPrompt(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="e.g., A login form with email and password fields..."
                                style={{
                                    width: '100%', height: 140, padding: '16px 16px 0',
                                    border: 'none', outline: 'none', resize: 'none',
                                    fontSize: 14, lineHeight: 1.6, color: '#0f172a',
                                    background: 'transparent', fontFamily: 'inherit',
                                    boxSizing: 'border-box'
                                }}
                            />
                            <div style={{ padding: '10px 12px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <span style={{ fontSize: 11, color: '#94a3b8' }}>⌘ + Enter to generate</span>
                                <button
                                    onClick={handleGenerate}
                                    disabled={loading || !prompt.trim()}
                                    style={{
                                        padding: '10px 22px', borderRadius: 10, border: 'none', cursor: loading || !prompt.trim() ? 'not-allowed' : 'pointer',
                                        background: loading || !prompt.trim() ? '#e2e8f0' : '#4f46e5',
                                        color: loading || !prompt.trim() ? '#94a3b8' : '#ffffff',
                                        fontWeight: 700, fontSize: 13, display: 'flex', alignItems: 'center', gap: 8,
                                        transition: 'all 0.15s ease', fontFamily: 'inherit'
                                    }}
                                >
                                    {loading ? (
                                        <>
                                            <svg width="14" height="14" viewBox="0 0 24 24" style={{ animation: 'spin 0.8s linear infinite' }}>
                                                <circle cx="12" cy="12" r="10" stroke="rgba(255,255,255,0.3)" strokeWidth="3" fill="none" />
                                                <path d="M12 2a10 10 0 0 1 10 10" stroke="white" strokeWidth="3" fill="none" strokeLinecap="round" />
                                            </svg>
                                            {result ? 'Refining...' : 'Generating...'}
                                        </>
                                    ) : (result ? 'Apply Change' : 'Generate')}
                                </button>
                            </div>
                        </div>

                        {/* Example prompts */}
                        {!result && (
                            <div>
                                <p style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>Try an example</p>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                                    {EXAMPLE_PROMPTS.map((ex, i) => (
                                        <button key={i} onClick={() => setPrompt(ex)}
                                            style={{
                                                textAlign: 'left', padding: '10px 14px', borderRadius: 10, cursor: 'pointer',
                                                background: '#ffffff', border: '1px solid #e2e8f0',
                                                fontSize: 13, color: '#475569', fontFamily: 'inherit',
                                                transition: 'all 0.12s ease'
                                            }}
                                            onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = '#4f46e5'; (e.currentTarget as HTMLButtonElement).style.color = '#4f46e5'; (e.currentTarget as HTMLButtonElement).style.background = '#eef2ff'; }}
                                            onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.borderColor = '#e2e8f0'; (e.currentTarget as HTMLButtonElement).style.color = '#475569'; (e.currentTarget as HTMLButtonElement).style.background = '#ffffff'; }}
                                        >
                                            {ex}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Stats */}
                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                            <div style={{ background: '#ffffff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '16px 18px', boxShadow: '0 1px 4px rgba(15,23,42,0.05)' }}>
                                <p style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', letterSpacing: '0.1em', textTransform: 'uppercase', margin: '0 0 6px' }}>Iterations</p>
                                <p style={{ fontSize: 28, fontWeight: 900, color: '#0f172a', margin: 0, letterSpacing: '-0.04em' }}>{result?.iterations ?? 0}</p>
                            </div>
                            <div style={{ background: '#ffffff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '16px 18px', boxShadow: '0 1px 4px rgba(15,23,42,0.05)' }}>
                                <p style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', letterSpacing: '0.1em', textTransform: 'uppercase', margin: '0 0 6px' }}>Status</p>
                                <p style={{ fontSize: 16, fontWeight: 700, color: statusColor, margin: 0 }}>{statusLabel}</p>
                            </div>
                        </div>

                        {/* History */}
                        {history.length > 0 && (
                            <div>
                                <p style={{ fontSize: 11, fontWeight: 600, color: '#94a3b8', letterSpacing: '0.08em', textTransform: 'uppercase', marginBottom: 8 }}>History</p>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
                                    {history.map((h, i) => (
                                        <button key={i} onClick={() => { setResult(h); setActiveTab('preview'); }}
                                            style={{
                                                display: 'flex', alignItems: 'center', gap: 10, padding: '10px 14px',
                                                borderRadius: 10, cursor: 'pointer', border: `1px solid ${result === h ? '#c7d2fe' : '#e2e8f0'}`,
                                                background: result === h ? '#eef2ff' : '#ffffff', fontFamily: 'inherit', textAlign: 'left',
                                                transition: 'all 0.12s ease'
                                            }}>
                                            <div style={{ width: 6, height: 6, borderRadius: '50%', background: h.success ? '#16a34a' : '#f59e0b', flexShrink: 0 }} />
                                            <span style={{ fontSize: 12, color: '#475569', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{h.prompt}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    {/* ── Right Panel ── */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>

                        {/* Tab bar */}
                        <div style={{ background: '#ffffff', borderRadius: '16px 16px 0 0', borderTop: '1px solid #e2e8f0', borderLeft: '1px solid #e2e8f0', borderRight: '1px solid #e2e8f0', padding: '0 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <div style={{ display: 'flex', gap: 2 }}>
                                {([['code', 'Source Code'], ['logs', 'Process Logs'], ['preview', 'Live Preview']] as const).map(([tab, label]) => (
                                    <button key={tab} onClick={() => setActiveTab(tab)}
                                        style={{
                                            padding: '14px 16px', border: 'none', cursor: 'pointer', fontFamily: 'inherit',
                                            fontSize: 13, fontWeight: activeTab === tab ? 700 : 500,
                                            color: activeTab === tab ? '#4f46e5' : '#94a3b8',
                                            background: 'transparent',
                                            borderBottom: activeTab === tab ? '2px solid #4f46e5' : '2px solid transparent',
                                            transition: 'all 0.12s ease'
                                        }}>
                                        {label}
                                    </button>
                                ))}
                            </div>
                            {result?.code && activeTab === 'code' && (
                                <button onClick={handleExport}
                                    style={{ fontSize: 12, fontWeight: 600, color: '#4f46e5', background: '#eef2ff', border: 'none', borderRadius: 8, padding: '6px 14px', cursor: 'pointer', fontFamily: 'inherit' }}>
                                    Export .ts
                                </button>
                            )}
                        </div>

                        {/* Window body */}
                        <div style={{ background: activeTab === 'code' ? '#ffffff' : activeTab === 'logs' ? '#0f172a' : '#f1f5f9', border: '1px solid #e2e8f0', borderTop: 'none', borderRadius: '0 0 16px 16px', height: 600, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>

                            {/* Traffic lights */}
                            <div style={{ padding: '10px 16px', borderBottom: `1px solid ${activeTab === 'logs' ? 'rgba(255,255,255,0.06)' : '#f1f5f9'}`, display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                                <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#fca5a5' }} />
                                <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#fcd34d' }} />
                                <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#86efac' }} />
                                <span style={{ marginLeft: 8, fontSize: 11, color: activeTab === 'logs' ? 'rgba(255,255,255,0.25)' : '#cbd5e1', fontWeight: 500, letterSpacing: '0.04em' }}>
                                    {activeTab === 'code' ? 'angular-component.ts' : activeTab === 'logs' ? 'agent-workflow.log' : 'live-preview.html'}
                                </span>
                            </div>

                            <div style={{ flex: 1, overflow: 'auto', minHeight: 0 }}>
                                {/* Source Code */}
                                {activeTab === 'code' && (
                                    result ? (
                                        <pre style={{ margin: 0, padding: '20px 24px', fontFamily: "'JetBrains Mono', 'Fira Code', monospace", fontSize: 12.5, lineHeight: 1.7, color: '#334155', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                                            <code>{result.code}</code>
                                        </pre>
                                    ) : (
                                        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, color: '#cbd5e1' }}>
                                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                                <path d="M8 9l3 3-3 3m5 0h3" strokeLinecap="round" strokeLinejoin="round" />
                                                <rect x="3" y="3" width="18" height="18" rx="3" />
                                            </svg>
                                            <p style={{ fontSize: 13, margin: 0, fontWeight: 500 }}>Generated code will appear here</p>
                                            <p style={{ fontSize: 12, margin: 0, color: '#e2e8f0' }}>Enter a prompt and click Generate</p>
                                        </div>
                                    )
                                )}

                                {/* Process Logs */}
                                {activeTab === 'logs' && (
                                    <div style={{ padding: '16px 20px' }}>
                                        {result?.logs?.length ? result.logs.map((log, i) => (
                                            <div key={i} style={{ display: 'flex', gap: 12, marginBottom: 10, paddingLeft: 12, borderLeft: '2px solid rgba(79,70,229,0.3)' }}>
                                                <span style={{ fontSize: 10, color: '#475569', flexShrink: 0, fontFamily: 'monospace' }}>
                                                    [{String(i + 1).padStart(2, '0')}]
                                                </span>
                                                <span style={{ fontSize: 11, color: '#4f46e5', fontWeight: 700, flexShrink: 0, fontFamily: 'monospace' }}>AGENT →</span>
                                                <span style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'monospace', lineHeight: 1.6 }}>{log}</span>
                                            </div>
                                        )) : (
                                            <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#334155' }}>
                                                <p style={{ fontSize: 13 }}>No logs yet. Run a generation.</p>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Live Preview */}
                                {activeTab === 'preview' && (
                                    result?.code ? (
                                        <iframe
                                            key={result.iterations + result.code.length}
                                            title="Live Preview"
                                            style={{ width: '100%', height: '100%', border: 'none', display: 'block' }}
                                            srcDoc={buildSrcDoc(result.code)}
                                            sandbox="allow-scripts"
                                        />
                                    ) : (
                                        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, color: '#cbd5e1' }}>
                                            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                                                <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" strokeLinecap="round" strokeLinejoin="round" />
                                                <path d="M2.458 12C3.732 7.943 7.523 5 12 5s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7s-8.268-2.943-9.542-7z" strokeLinecap="round" strokeLinejoin="round" />
                                            </svg>
                                            <p style={{ fontSize: 13, margin: 0, fontWeight: 500 }}>Live preview will appear here</p>
                                            <p style={{ fontSize: 12, margin: 0, color: '#e2e8f0' }}>Generate a component first</p>
                                        </div>
                                    )
                                )}
                            </div>
                        </div>

                        {/* Status bar */}
                        <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '0 4px' }}>
                            <span style={{ fontSize: 11, color: '#94a3b8' }}>
                                {result ? `Design System v3.0 · ${result.iterations} iteration${result.iterations !== 1 ? 's' : ''}` : 'Powered by Groq LLaMA-3 · Design System v3.0'}
                            </span>
                            {result && (
                                <span style={{ fontSize: 11, fontWeight: 600, color: result.success ? '#16a34a' : '#d97706', display: 'flex', alignItems: 'center', gap: 5 }}>
                                    <span style={{ width: 6, height: 6, borderRadius: '50%', background: result.success ? '#16a34a' : '#d97706', display: 'inline-block' }} />
                                    {result.success ? 'Validation passed' : 'Needs review'}
                                </span>
                            )}
                        </div>
                    </div>
                </div>
            </main>

            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
                * { box-sizing: border-box; }
                textarea::placeholder { color: #94a3b8; }
                textarea { outline: none; }
                /* Hide scrollbar on left panel but keep it scrollable */
                .left-panel::-webkit-scrollbar { display: none; }
                .left-panel { scrollbar-width: none; -ms-overflow-style: none; }
            `}</style>
        </div>
    );
};

export default App;
