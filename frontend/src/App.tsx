import React, { useState } from 'react';

interface GenerationResult {
    code: string;
    iterations: number;
    logs: string[];
    success: boolean;
}

const App = () => {
    const [prompt, setPrompt] = useState<string>('');
    const [result, setResult] = useState<GenerationResult | null>(null);
    const [loading, setLoading] = useState<boolean>(false);

    const [activeTab, setActiveTab] = useState<'code' | 'logs'>('code');

    const handleGenerate = async () => {
        setLoading(true);
        setActiveTab('logs'); // Switch to logs view when starting generation
        try {
            const response = await fetch('http://localhost:8080/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    prompt,
                    prev_code: result?.code // Pass existing code for multi-turn editing
                }),
            });
            const data: GenerationResult = await response.json();
            setResult(data);
            setPrompt(''); // Clear prompt after send
            setActiveTab('code'); // Switch back to code after success
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
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
            {/* Header */}
            <header className="border-b border-gray-200 bg-white/80 backdrop-blur-md sticky top-0 z-50">
                <div className="max-w-6xl mx-auto px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-9 h-9 bg-[#2563eb] rounded-lg flex items-center justify-center shadow-sm">
                            <span className="text-white font-bold text-lg">A</span>
                        </div>
                        <h1 className="text-lg font-bold tracking-tight text-gray-900">Component Architect</h1>
                    </div>
                    <div className="flex items-center gap-5">
                        <div className="flex items-center gap-2 text-sm font-medium text-gray-500">
                            <div className="w-2 h-2 rounded-full bg-green-500"></div>
                            <span>Connected</span>
                        </div>
                    </div>
                </div>
            </header>

            <main className="max-w-6xl mx-auto px-6 py-12">
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">
                    {/* Left Column: Input (5 columns) */}
                    <div className="lg:col-span-5 space-y-8">
                        <div className="space-y-3">
                            <h2 className="text-4xl font-extrabold tracking-tight text-gray-900">
                                {result ? "Refine your component." : "Build your ideas in Angular."}
                            </h2>
                            <p className="text-lg text-gray-600 leading-relaxed max-w-md">
                                {result ? "Ask for changes like 'add a rounded border' or 'change colors to indigo'." : "Describe the component you need. Our system will generate it based on your design rules."}
                            </p>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden p-1">
                            <div className="p-4">
                                <textarea
                                    value={prompt}
                                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
                                    placeholder={result ? "e.g., Now make the button fully rounded..." : "e.g., A clean login form with email and password fields..."}
                                    className="w-full h-48 bg-transparent border-none focus:ring-0 text-gray-800 placeholder:text-gray-400 resize-none text-base leading-relaxed"
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
                                    ) : (result ? 'Update Component' : 'Create Component')}
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-5 rounded-xl bg-white border border-gray-200 shadow-sm">
                                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1">Total Retries</p>
                                <p className="text-2xl font-bold text-gray-900">{result?.iterations || 0}</p>
                            </div>
                            <div className="p-5 rounded-xl bg-white border border-gray-200 shadow-sm">
                                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1">Status</p>
                                <p className={`text-xl font-bold ${result?.success ? 'text-green-600' : (result ? 'text-amber-600' : 'text-gray-900')}`}>
                                    {result ? (result.success ? 'Verified' : 'Refining...') : 'Standby'}
                                </p>
                            </div>
                        </div>
                    </div>

                    {/* Right Column: Viewer (7 columns) */}
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
                                    {activeTab === 'code' ? 'angular-component.ts' : 'agent-workflow.log'}
                                </span>
                            </div>

                            <div className={`flex-1 overflow-auto ${activeTab === 'logs' ? 'bg-gray-900 p-0' : 'bg-white p-6'}`}>
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
                                ) : (
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
