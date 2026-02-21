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

    const handleGenerate = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8080/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt }),
            });
            const data: GenerationResult = await response.json();
            setResult(data);
        } catch (error) {
            console.error('Error:', error);
        } finally {
            setLoading(false);
        }
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
                                Build your ideas in Angular.
                            </h2>
                            <p className="text-lg text-gray-600 leading-relaxed max-w-md">
                                Describe the component you need. Our system will generate and validate it against your design rules.
                            </p>
                        </div>

                        <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden p-1">
                            <div className="p-4">
                                <textarea
                                    value={prompt}
                                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setPrompt(e.target.value)}
                                    placeholder="e.g., A clean login form with email and password fields, using soft borders..."
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
                                            Generating...
                                        </>
                                    ) : 'Create Component'}
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-5 rounded-xl bg-white border border-gray-200 shadow-sm">
                                <p className="text-[11px] font-bold text-gray-400 uppercase tracking-widest mb-1">Iterations</p>
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

                    {/* Right Column: Code (7 columns) */}
                    <div className="lg:col-span-7 space-y-6">
                        <div className="flex items-center gap-6 border-b border-gray-200">
                            <button className="text-sm font-bold text-gray-900 border-b-2 border-[#2563eb] pb-3 px-1">Source Code</button>
                            <button className="text-sm font-bold text-gray-400 pb-3 px-1 hover:text-gray-600 transition-colors">Process Logs</button>
                        </div>

                        <div className="bg-white rounded-2xl border border-gray-200 shadow-xl overflow-hidden flex flex-col h-[600px]">
                            <div className="px-4 py-3 bg-gray-50/50 border-b border-gray-200 flex items-center justify-between">
                                <div className="flex gap-1.5">
                                    <div className="w-2.5 h-2.5 rounded-full bg-gray-300"></div>
                                    <div className="w-2.5 h-2.5 rounded-full bg-gray-300"></div>
                                    <div className="w-2.5 h-2.5 rounded-full bg-gray-300"></div>
                                </div>
                                <span className="text-[11px] font-bold text-gray-400 uppercase tracking-widest">angular-component.ts</span>
                            </div>

                            <div className="flex-1 overflow-auto p-6 bg-white">
                                {result ? (
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
                                )}
                            </div>

                            {result?.logs && (
                                <div className="p-4 bg-gray-900 border-t border-gray-800 h-40 overflow-auto scrollbar-thin scrollbar-thumb-gray-700">
                                    {result.logs.map((log: string, i: number) => (
                                        <div key={i} className="text-[11px] font-mono text-gray-400 flex gap-3 mb-1.5 last:mb-0">
                                            <span className="text-gray-600 shrink-0">{new Date().toLocaleTimeString([], { hour12: false })}</span>
                                            <span className="text-gray-300">{log}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
};

export default App;
