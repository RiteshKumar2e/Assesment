import React, { useState } from 'react';

interface GenerationResult {
    code: string;
    iterations: number;
    logs: string[];
    success: boolean;
    prompt?: string;
}

const App = () => {
    const [prompt, setPrompt] = useState<string>('');
    const [result, setResult] = useState<GenerationResult | null>(null);
    const [loading, setLoading] = useState<boolean>(false);
    const [history, setHistory] = useState<GenerationResult[]>([]);

    const [activeTab, setActiveTab] = useState<'code' | 'logs' | 'preview'>('code');

    const handleGenerate = async () => {
        setLoading(true);
        setActiveTab('logs');
        try {
            const response = await fetch('http://localhost:8080/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt,
                    prev_code: result?.code
                }),
            });
            const data: GenerationResult = await response.json();
            const resultWithPrompt = { ...data, prompt };
            setResult(resultWithPrompt);
            setHistory(prev => [resultWithPrompt, ...prev].slice(0, 5));
            setPrompt('');
            setActiveTab('code');
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleClear = () => {
        setPrompt('');
        setResult(null);
        setHistory([]);
        setActiveTab('code');
    };

    const handleExport = () => {
        if (!result?.code) return;
        const blob = new Blob([result.code], { type: 'text/typescript' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'generated-component.tsx';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="min-h-screen bg-[#fcfcfd] text-[#1a1c1e] font-sans selection:bg-[#4f46e5]/10">
            <header className="border-b border-gray-200 bg-white/80 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-[#2563eb] rounded-lg flex items-center justify-center shadow-sm">
                            <span className="text-white font-bold text-lg">A</span>
                        </div>
                        <h1 className="text-lg font-bold tracking-tight text-gray-900">Component Architect</h1>
                    </div>
                    <div className="flex items-center gap-5">
                        {result && (
                            <button
                                onClick={handleClear}
                                className="text-xs font-bold text-red-500 hover:text-red-600 transition-colors uppercase tracking-widest px-3 py-1 border border-red-100 rounded-full hover:bg-red-50"
                            >
                                Clear Session
                            </button>
                        )}
                        <div className="flex items-center gap-2 text-sm font-medium text-gray-500">
                            <div className="w-2 h-2 rounded-full bg-green-500"></div>
                            <span>Connected</span>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-6xl mx-auto px-6 py-12">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                    <div className="lg:col-span-5 space-y-8">
                        <div className="space-y-3">
                            <h2 className="text-4xl font-extrabold tracking-tight text-gray-900">
                                {result ? "Refine component." : "Build your ideas."}
                            </h2>
                            <p className="text-lg text-gray-600 leading-relaxed max-w-sm">
                                {result ? "Request a change or adjustment to the current version." : "Describe the component you need. Our system will follow your design rules."}
                            </p>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden p-1">
                            <div className="p-4">
                                <textarea
                                    value={prompt}
                                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
                                    placeholder={result ? "e.g., Now make the button fully rounded..." : "e.g., A clean login form with email and password fields..."}
                                    className="w-full h-40 bg-transparent border-none focus:ring-0 text-gray-800 placeholder:text-gray-400 resize-none text-base leading-relaxed"
                                />
                            </div>
                            <div className="bg-gray-50 p-3 flex justify-end border-t border-gray-100">
                                <button
                                    onClick={handleGenerate}
                                    disabled={loading || !prompt}
                                    className="px-6 py-2.5 bg-[#2563eb] hover:bg-[#1d4ed8] disabled:bg-gray-200 disabled:text-gray-400 text-white font-semibold rounded-lg transition-colors shadow-sm flex items-center gap-2 text-sm"
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                            {result ? 'Updating...' : 'Generating...'}
                                        </>
                                    ) : (result ? 'Apply Change' : 'Create Component')}
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-5 rounded-xl bg-white border border-gray-200 shadow-sm">
                                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1">Self-Corrections</p>
                                <p className="text-2xl font-bold text-gray-900">{result?.iterations || 0}</p>
                            </div>
                            <div className="p-5 rounded-xl bg-white border border-gray-200 shadow-sm">
                                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1">Status</p>
                                <p className={`text-xl font-bold ${result?.success ? 'text-green-600' : (result ? 'text-amber-600' : 'text-gray-900')}`}>
                                    {result ? (result.success ? 'Verified' : 'Refining...') : 'Ready'}
                                </p>
                            </div>
                        </div>

                        {history.length > 0 && (
                            <div className="space-y-4 pt-4 border-t border-gray-100">
                                <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Session History</h3>
                                <div className="space-y-2">
                                    {history.map((h, i) => (
                                        <button
                                            key={i}
                                            onClick={() => { setResult(h); setActiveTab('code'); }}
                                            className={`w-full text-left p-3 rounded-lg border transition-all flex items-center justify-between group ${result === h ? 'bg-blue-50 border-blue-200' : 'bg-white border-gray-100 hover:border-gray-300'}`}
                                        >
                                            <div className="flex items-center gap-3 w-full overflow-hidden">
                                                <div className={`w-2 h-2 shrink-0 rounded-full ${h.success ? 'bg-green-500' : 'bg-amber-500'}`}></div>
                                                <span className="text-sm font-medium text-gray-700 truncate flex-1">{h.prompt || "Generated Component"}</span>
                                            </div>
                                            <span className="text-[10px] text-gray-400 font-mono opacity-0 group-hover:opacity-100 transition-opacity">RESTORE</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="lg:col-span-7 space-y-6">
                        <div className="flex items-center justify-between border-b border-gray-200">
                            <div className="flex items-center gap-6">
                                <button
                                    onClick={() => setActiveTab('code')}
                                    className={`text-sm font-bold pb-3 px-1 transition-colors ${activeTab === 'code' ? 'text-gray-900 border-b-2 border-[#2563eb]' : 'text-gray-400 hover:text-gray-600'}`}
                                >
                                    Source Code
                                </button>
                                <button
                                    onClick={() => setActiveTab('logs')}
                                    className={`text-sm font-bold pb-3 px-1 transition-colors ${activeTab === 'logs' ? 'text-gray-900 border-b-2 border-[#2563eb]' : 'text-gray-400 hover:text-gray-600'}`}
                                >
                                    Process Logs
                                </button>
                                <button
                                    onClick={() => setActiveTab('preview')}
                                    className={`text-sm font-bold pb-3 px-1 transition-colors ${activeTab === 'preview' ? 'text-gray-900 border-b-2 border-[#2563eb]' : 'text-gray-400 hover:text-gray-600'}`}
                                >
                                    Live Preview
                                </button>
                            </div>
                            {result?.code && activeTab === 'code' && (
                                <button
                                    onClick={handleExport}
                                    className="mb-2 text-xs font-bold text-[#2563eb] hover:text-[#1d4ed8] flex items-center gap-1.5 transition-colors"
                                >
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a2 2 0 002 2h12a2 2 0 002-2v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                                    </svg>
                                    Export .tsx
                                </button>
                            )}
                        </div>

                        <div className="bg-white rounded-2xl border border-gray-200 shadow-xl overflow-hidden flex flex-col h-[600px]">
                            <div className="px-4 py-3 bg-gray-50/50 border-b border-gray-200 flex items-center justify-between">
                                <div className="flex gap-1.5">
                                    <div className="w-2.5 h-2.5 rounded-full bg-gray-300"></div>
                                    <div className="w-2.5 h-2.5 rounded-full bg-gray-300"></div>
                                    <div className="w-2.5 h-2.5 rounded-full bg-gray-300"></div>
                                </div>
                                <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">
                                    {activeTab === 'code' ? 'angular-component.ts' : (activeTab === 'logs' ? 'agent-workflow.log' : 'preview-rendering.html')}
                                </span>
                            </div>

                            <div className={`flex-1 overflow-auto ${activeTab === 'logs' ? 'bg-gray-900 p-0' : (activeTab === 'preview' ? 'bg-[#fcfcfd]' : 'bg-white p-6')}`}>
                                {activeTab === 'code' ? (
                                    result ? (
                                        <pre className="font-mono text-[13px] leading-relaxed text-blue-900/80 antialiased whitespace-pre-wrap">
                                            <code>{result.code}</code>
                                        </pre>
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-gray-300 select-none space-y-4">
                                            <div className="w-16 h-16 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-center">
                                                <svg className="w-8 h-8 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                                                </svg>
                                            </div>
                                            <p className="text-sm font-medium">Your generated code will appear here</p>
                                        </div>
                                    )
                                ) : activeTab === 'logs' ? (
                                    <div className="p-6 font-mono text-[11px] h-full overflow-auto">
                                        {result?.logs ? (
                                            result.logs.map((log: string, i: number) => (
                                                <div key={i} className="flex gap-3 mb-2 last:mb-0 border-l-2 border-gray-800 pl-3">
                                                    <span className="text-gray-600 shrink-0 select-none">[{new Date().toLocaleTimeString([], { hour12: false })}]</span>
                                                    <span className="text-blue-400 font-bold select-none whitespace-nowrap">AGENT →</span>
                                                    <span className="text-gray-300">{log}</span>
                                                </div>
                                            ))
                                        ) : (
                                            <div className="h-full flex flex-col items-center justify-center text-gray-600 select-none">
                                                <p>No activity logs found.</p>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="h-full flex flex-col items-center justify-center p-6 bg-white overflow-auto scrollbar-hide">
                                        {result ? (
                                            <div className="w-full max-w-md animate-in fade-in zoom-in duration-500">
                                                <div className="mb-6 text-center">
                                                    <div className="inline-flex items-center gap-2 px-2 py-1 rounded bg-green-50 text-green-600 text-[9px] font-bold uppercase tracking-tighter mb-2 border border-green-100">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
                                                        Token Validated Render
                                                    </div>
                                                    <h3 className="text-lg font-black text-gray-900 leading-none truncate capitalize">
                                                        {result.prompt?.toLowerCase().includes('login') ? 'Secure Portal' :
                                                            result.prompt?.toLowerCase().includes('card') ? 'Interactive Profile' :
                                                                result.prompt?.toLowerCase().includes('dashboard') ? 'System Analytics' :
                                                                    result.prompt?.toLowerCase().includes('list') ? 'Data Infrastructure' :
                                                                        'Component Architected'}
                                                    </h3>
                                                </div>

                                                {/* The "Live" Mockup */}
                                                <div className="bg-[#0f172a] rounded-[32px] p-6 shadow-2xl border border-white/5 space-y-6">
                                                    {result.prompt?.toLowerCase().includes('login') ? (
                                                        <div className="space-y-4">
                                                            <div className="h-10 w-10 bg-[#6366f1] rounded-2xl mx-auto mb-6 shadow-xl rotate-3"></div>
                                                            <div className="space-y-3">
                                                                <div className="h-10 w-full bg-white/5 border border-white/10 rounded-xl"></div>
                                                                <div className="h-10 w-full bg-white/5 border border-white/10 rounded-xl"></div>
                                                            </div>
                                                            <div className="h-12 w-full bg-[#6366f1] rounded-xl flex items-center justify-center shadow-lg shadow-indigo-500/30">
                                                                <span className="text-white font-black text-xs tracking-widest">AUTHENTICATE</span>
                                                            </div>
                                                        </div>
                                                    ) : result.prompt?.toLowerCase().includes('card') ? (
                                                        <div className="space-y-5">
                                                            <div className="aspect-[16/10] w-full bg-gradient-to-br from-[#6366f1]/20 to-purple-600/20 rounded-2xl border border-white/10 flex items-center justify-center">
                                                                <svg className="w-14 h-14 text-[#6366f1]/40" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" /></svg>
                                                            </div>
                                                            <div className="space-y-2">
                                                                <div className="h-4 w-2/3 bg-white/20 rounded-full"></div>
                                                                <div className="h-2 w-full bg-white/5 rounded-full"></div>
                                                                <div className="h-2 w-full bg-white/5 rounded-full"></div>
                                                            </div>
                                                            <div className="flex justify-between items-center pt-2">
                                                                <div className="h-6 w-16 bg-white/10 rounded-lg"></div>
                                                                <div className="h-9 w-24 bg-white rounded-xl"></div>
                                                            </div>
                                                        </div>
                                                    ) : result.prompt?.toLowerCase().includes('dashboard') ? (
                                                        <div className="space-y-6">
                                                            <div className="flex justify-between items-center">
                                                                <div className="h-4 w-24 bg-white/20 rounded-full"></div>
                                                                <div className="w-8 h-8 rounded-full bg-green-500/20 border border-green-500/40 flex items-center justify-center">
                                                                    <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                                                                </div>
                                                            </div>
                                                            <div className="grid grid-cols-3 gap-3">
                                                                {[1, 2, 3].map(i => (
                                                                    <div key={i} className={`h-20 ${i === 2 ? 'bg-[#6366f1]' : 'bg-white/5'} rounded-2xl border border-white/10 p-3 space-y-2`}>
                                                                        <div className="h-1.5 w-1/2 bg-white/10 rounded"></div>
                                                                        <div className="h-4 w-full bg-white/20 rounded mt-auto"></div>
                                                                    </div>
                                                                ))}
                                                            </div>
                                                            <div className="h-32 bg-white/5 border border-white/10 rounded-2xl flex items-end p-4 gap-2">
                                                                {[40, 70, 50, 90, 60, 80].map((h, i) => (
                                                                    <div key={i} style={{ height: `${h}%` }} className="flex-1 bg-[#6366f1]/30 rounded-t-sm"></div>
                                                                ))}
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div className="space-y-8 py-8 px-4 text-center">
                                                            <div className="inline-flex items-center gap-3 px-4 py-2 bg-[#6366f1]/10 border border-[#6366f1]/20 rounded-full">
                                                                <span className="w-2 h-2 rounded-full bg-[#6366f1] animate-pulse"></span>
                                                                <span className="text-[#6366f1] text-[10px] font-black uppercase tracking-widest">Active Render</span>
                                                            </div>
                                                            <div className="space-y-4">
                                                                <h1 className="text-3xl font-black text-white leading-tight tracking-tighter">
                                                                    {result.prompt}
                                                                </h1>
                                                                <div className="h-1 w-20 bg-[#6366f1] mx-auto rounded-full opacity-50"></div>
                                                            </div>
                                                            <p className="text-white/40 text-sm leading-relaxed max-w-xs mx-auto italic">
                                                                Proprietary architecture generated via agentic loop iteration {result.iterations}.
                                                            </p>
                                                            <button className="w-full py-4 bg-white text-[#0f172a] font-black rounded-2xl text-[10px] tracking-[0.3em] uppercase transition-all hover:scale-[1.02] active:scale-95 shadow-xl shadow-white/5">
                                                                Initialize Instance
                                                            </button>
                                                        </div>
                                                    )}
                                                </div>

                                                {/* Specs Footer */}
                                                <div className="mt-8 grid grid-cols-3 gap-4">
                                                    <div className="text-center">
                                                        <p className="text-[8px] font-bold text-gray-400 uppercase tracking-widest mb-1">Theme</p>
                                                        <div className="flex justify-center gap-1">
                                                            <div className="w-3 h-3 rounded-full bg-[#6366f1]"></div>
                                                            <div className="w-3 h-3 rounded-full bg-[#0f172a] border border-gray-200"></div>
                                                        </div>
                                                    </div>
                                                    <div className="text-center border-x border-gray-100">
                                                        <p className="text-[8px] font-bold text-gray-400 uppercase tracking-widest mb-1">State</p>
                                                        <span className="text-[10px] font-bold text-green-600">Production</span>
                                                    </div>
                                                    <div className="text-center">
                                                        <p className="text-[8px] font-bold text-gray-400 uppercase tracking-widest mb-1">Logic</p>
                                                        <span className="text-[10px] font-bold text-gray-900">Standalone</span>
                                                    </div>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="h-full flex flex-col items-center justify-center text-gray-300 select-none space-y-4">
                                                <div className="w-16 h-16 rounded-2xl bg-gray-50 border border-gray-100 flex items-center justify-center">
                                                    <svg className="w-8 h-8 text-gray-200" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                                                    </svg>
                                                </div>
                                                <p className="text-sm font-medium">System idle. Please provide a prompt.</p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default App;
