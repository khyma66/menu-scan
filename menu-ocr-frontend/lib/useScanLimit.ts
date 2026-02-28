import { useState, useEffect, useCallback } from "react";
import type { UserTier } from "@/types/menu";

const SCAN_COUNT_KEY = "menu_ocr_scan_count";
const USER_TIER_KEY = "menu_ocr_user_tier";
const FREE_SCAN_LIMIT = 3;

export function useScanLimit() {
    const [scanCount, setScanCount] = useState(0);
    const [userTier, setUserTier] = useState<UserTier>("free");
    const [showUpgradeModal, setShowUpgradeModal] = useState(false);

    useEffect(() => {
        const storedCount = parseInt(localStorage.getItem(SCAN_COUNT_KEY) || "0", 10);
        const storedTier = (localStorage.getItem(USER_TIER_KEY) as UserTier) || "free";
        setScanCount(storedCount);
        setUserTier(storedTier);
    }, []);

    const canScan = useCallback((): boolean => {
        if (userTier === "pro" || userTier === "max") return true;
        return scanCount < FREE_SCAN_LIMIT;
    }, [userTier, scanCount]);

    const incrementScan = useCallback(() => {
        const newCount = scanCount + 1;
        setScanCount(newCount);
        localStorage.setItem(SCAN_COUNT_KEY, newCount.toString());
    }, [scanCount]);

    const getRemainingScans = useCallback((): number => {
        if (userTier === "pro" || userTier === "max") return Infinity;
        return Math.max(0, FREE_SCAN_LIMIT - scanCount);
    }, [userTier, scanCount]);

    const upgradeTier = useCallback((tier: UserTier) => {
        setUserTier(tier);
        localStorage.setItem(USER_TIER_KEY, tier);
        setShowUpgradeModal(false);
    }, []);

    const promptUpgrade = useCallback(() => {
        setShowUpgradeModal(true);
    }, []);

    return {
        scanCount,
        userTier,
        canScan,
        incrementScan,
        getRemainingScans,
        upgradeTier,
        showUpgradeModal,
        setShowUpgradeModal,
        promptUpgrade,
        FREE_SCAN_LIMIT,
    };
}
