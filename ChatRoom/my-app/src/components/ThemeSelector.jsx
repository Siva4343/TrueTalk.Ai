import { useState } from 'react';

const THEMES = [
    { id: 'default', name: 'Default', bg: 'bg-black', bubble: 'bg-blue-600' },
    { id: 'ocean', name: 'Ocean', bg: 'bg-slate-900', bubble: 'bg-cyan-600' },
    { id: 'forest', name: 'Forest', bg: 'bg-green-950', bubble: 'bg-emerald-600' },
    { id: 'sunset', name: 'Sunset', bg: 'bg-rose-950', bubble: 'bg-orange-600' },
    { id: 'midnight', name: 'Midnight', bg: 'bg-indigo-950', bubble: 'bg-violet-600' },
];

export default function ThemeSelector({ currentTheme, onSelect, onClose }) {
    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center" onClick={onClose}>
            <div className="bg-gray-900 rounded-xl p-6 w-80 border border-gray-800" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-semibold text-white">Select Theme</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                <div className="grid grid-cols-2 gap-3">
                    {THEMES.map(theme => (
                        <button
                            key={theme.id}
                            onClick={() => onSelect(theme.id)}
                            className={`p-3 rounded-lg border-2 transition-all ${currentTheme === theme.id ? 'border-blue-500' : 'border-transparent hover:border-gray-700'
                                }`}
                        >
                            <div className={`h-16 rounded-md mb-2 ${theme.bg} flex items-center justify-center`}>
                                <div className={`w-8 h-6 rounded-lg ${theme.bubble}`}></div>
                            </div>
                            <span className="text-sm text-gray-300">{theme.name}</span>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
