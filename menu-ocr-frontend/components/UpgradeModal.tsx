"use client";

import type { UserTier } from "@/types/menu";

interface UpgradeModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUpgrade: (tier: UserTier) => void;
    scanCount: number;
    freeLimit: number;
}

export default function UpgradeModal({
    isOpen,
    onClose,
    onUpgrade,
    scanCount,
    freeLimit,
}: UpgradeModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            {/* Modal */}
            <div className="relative bg-white rounded-2xl shadow-2xl max-w-lg w-full mx-4 overflow-hidden">
                {/* Header */}
                <div className="bg-gradient-to-r from-purple-600 to-indigo-600 px-6 py-5 text-white">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-bold">Upgrade Your Plan</h2>
                            <p className="text-sm text-purple-200 mt-1">
                                You've used {scanCount}/{freeLimit} free scans
                            </p>
                        </div>
                        <button onClick={onClose} className="text-white/80 hover:text-white text-2xl">×</button>
                    </div>
                    {/* Progress Bar */}
                    <div className="mt-3 bg-purple-800/40 rounded-full h-2">
                        <div
                            className="bg-white rounded-full h-2 transition-all duration-500"
                            style={{ width: `${Math.min(100, (scanCount / freeLimit) * 100)}%` }}
                        />
                    </div>
                </div>

                {/* Plans */}
                <div className="p-6 space-y-4">
                    {/* Pro Plan */}
                    <div
                        onClick={() => onUpgrade("pro")}
                        className="border-2 border-blue-200 rounded-xl p-4 cursor-pointer hover:border-blue-400 hover:shadow-md transition-all group"
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="text-lg">⚡</span>
                                    <h3 className="font-bold text-gray-900 text-lg">Pro</h3>
                                </div>
                                <p className="text-sm text-gray-600 mt-1">Unlimited scans • Basic dish details</p>
                            </div>
                            <span className="text-xs px-3 py-1 bg-blue-100 text-blue-700 rounded-full font-semibold group-hover:bg-blue-200 transition">
                                Activate
                            </span>
                        </div>
                        <ul className="mt-3 space-y-1">
                            <li className="text-xs text-gray-500 flex items-center gap-1">
                                <span className="text-green-500">✓</span> Unlimited menu scans
                            </li>
                            <li className="text-xs text-gray-500 flex items-center gap-1">
                                <span className="text-green-500">✓</span> Name, Price, Category, Description
                            </li>
                            <li className="text-xs text-gray-500 flex items-center gap-1">
                                <span className="text-green-500">✓</span> Recommendation & reason
                            </li>
                            <li className="text-xs text-gray-400 flex items-center gap-1">
                                <span className="text-gray-300">✗</span> Ingredients, Allergens, Similar Dishes hidden
                            </li>
                        </ul>
                    </div>

                    {/* Max Plan */}
                    <div
                        onClick={() => onUpgrade("max")}
                        className="border-2 border-purple-300 rounded-xl p-4 cursor-pointer hover:border-purple-500 hover:shadow-md transition-all bg-gradient-to-br from-purple-50 to-indigo-50 group relative"
                    >
                        <span className="absolute -top-2 right-4 bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full uppercase">
                            Best Value
                        </span>
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="text-lg">👑</span>
                                    <h3 className="font-bold text-gray-900 text-lg">Max</h3>
                                </div>
                                <p className="text-sm text-gray-600 mt-1">Everything in Pro + full AI details</p>
                            </div>
                            <span className="text-xs px-3 py-1 bg-purple-100 text-purple-700 rounded-full font-semibold group-hover:bg-purple-200 transition">
                                Activate
                            </span>
                        </div>
                        <ul className="mt-3 space-y-1">
                            <li className="text-xs text-gray-500 flex items-center gap-1">
                                <span className="text-green-500">✓</span> Everything in Pro
                            </li>
                            <li className="text-xs text-gray-500 flex items-center gap-1">
                                <span className="text-green-500">✓</span> Full Ingredients list
                            </li>
                            <li className="text-xs text-gray-500 flex items-center gap-1">
                                <span className="text-green-500">✓</span> Allergen warnings
                            </li>
                            <li className="text-xs text-gray-500 flex items-center gap-1">
                                <span className="text-green-500">✓</span> Similar dishes from world cuisines
                            </li>
                        </ul>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 pb-5 text-center">
                    <button
                        onClick={onClose}
                        className="text-xs text-gray-400 hover:text-gray-600 transition"
                    >
                        Maybe later
                    </button>
                </div>
            </div>
        </div>
    );
}
