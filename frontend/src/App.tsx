import React, { useState } from 'react';

const App = () => {
    const [prompt, setPrompt] = useState('');
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt }),
            });
            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-[#0f172a] text-[#f8fafc] font-sans selection:bg-[#6366f1]/30">
            {/* Header */}
            <header className="border-b border-white/5 bg-[#0f172a]/80 backdrop-blur-xl sticky top-0 z-50">
                <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gradient-to-tr from-[#6366f1] to-[#a855f7] rounded-xl flex items-center justify-center shadow-lg shadow-[#6366f1]/20">
                            <span className="text-xl font-bold">A</span>
                        </div>
                        <h1 className="text-xl font-semibold tracking-tight">Guided Component Architect</h1>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-[#f8fafc]/60">
                        <span className="flex items-center gap-1.5"><div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div> Backend Online</span>
                    </div>
                </div>
            </header>

            <main className="max-w-7xl mx-auto px-6 py-12 grid grid-cols-1 lg:grid-cols-2 gap-12">
                {/* Left Column: Input */}
                <div className="space-y-8">
                    <div className="space-y-4">
                        <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-white/60">
                            Transform Ideas into Angular.
                        </h2>
                        <p className="text-lg text-[#f8fafc]/60 leading-relaxed">
                            Describe your component in natural language. Our agents will generate, validate, and polish the code according to your design system.
                        </p>
                    </div>

                    <div className="relative group">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-[#6366f1] to-[#a855f7] rounded-2xl blur opacity-20 group-focus-within:opacity-40 transition duration-1000"></div>
                        <div className="relative bg-[#1e293b]/50 backdrop-blur-xl border border-white/10 rounded-2xl p-6">
                            <textarea
                                value={prompt}
                                onChange={(e) => setPrompt(e.target.value)}
                                placeholder="e.g., A login card with glassmorphism effect and indigo primary buttons..."
                                className="w-full h-48 bg-transparent border-none focus:ring-0 text-lg resize-none placeholder:text-white/20"
                            />
                            <div className="mt-4 flex justify-end">
                                <button
                                    onClick={handleGenerate}
                                    disabled={loading || !prompt}
                                    className="px-8 py-3 bg-[#6366f1] hover:bg-[#4f46e5] disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all shadow-lg shadow-[#6366f1]/25 flex items-center gap-2"
                                >
                                    {loading ? (
                                        <>
                                            <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                                            Architecting...
                                        </>
                                    ) : 'Generate Component'}
                                </button>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                            <p className="text-xs font-medium text-white/40 uppercase tracking-wider mb-1">Total Retries</p>
                            <p className="text-2xl font-semibold">{result?.iterations || 0}</p>
                        </div>
                        <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
                            <p className="text-xs font-medium text-white/40 uppercase tracking-wider mb-1">Validation Status</p>
                            <p className={`text-2xl font-semibold ${result?.success ? 'text-green-400' : 'text-orange-400'}`}>
                                {result ? (result.success ? 'Passed' : 'Correcting...') : 'Ready'}
                            </p>
                        </div>
                    </div>
                </div>

                {/* Right Column: Output & Logs */}
                <div className="space-y-6">
                    <div className="flex items-center gap-4 border-b border-white/10 pb-2">
                        <button className="text-sm font-semibold border-b-2 border-[#6366f1] pb-2 px-2">Generated Code</button>
                        <button className="text-sm font-semibold text-white/40 pb-2 px-2">Agent Logs</button>
                    </div>

                    <div className="bg-[#020617] rounded-2xl border border-white/10 overflow-hidden h-[600px] flex flex-col">
                        <div className="flex items-center gap-2 px-4 py-2 bg-white/5 border-b border-white/10">
                            <div className="w-3 h-3 rounded-full bg-red-500/20"></div>
                            <div className="w-3 h-3 rounded-full bg-yellow-500/20"></div>
                            <div className="w-3 h-3 rounded-full bg-green-500/20"></div>
                            <span className="ml-4 text-xs font-mono text-white/40">generated-component.ts</span>
                        </div>
                        <div className="flex-1 overflow-auto p-6 font-mono text-sm leading-relaxed text-indigo-300">
                            {result ? (
                                <pre>{result.code}</pre>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-white/20 select-none">
                                    <div className="text-4xl mb-4 opacity-10">/ /</div>
                                    <p>Awaiting architecture details...</p>
                                </div>
                            )}
                        </div>
                        {result?.logs && (
                            <div className="p-4 bg-black/40 border-t border-white/10 max-h-40 overflow-auto">
                                {result.logs.map((log, i) => (
                                    <div key={i} className="text-[10px] font-mono text-white/40 flex gap-2">
                                        <span className="text-[#6366f1] shrink-0">[{new Date().toLocaleTimeString()}]</span>
                                        <span>{log}</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </main>
        </div>
    );
};

export default App;
