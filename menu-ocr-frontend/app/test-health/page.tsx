"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { ocrApi } from "@/lib/api";

export default function TestHealthPage() {
  const [status, setStatus] = useState<string>("");
  const [token, setToken] = useState<string>("");
  const [conditions, setConditions] = useState<any[]>([]);

  const testAuth = async () => {
    try {
      const { data: { session }, error } = await supabase.auth.getSession();
      if (error) {
        setStatus(`❌ Session Error: ${error.message}`);
        return;
      }
      if (session) {
        setToken(session.access_token || "No token");
        setStatus(`✅ Session OK. User: ${session.user.email}`);
      } else {
        setStatus("⚠️ No session. Please sign in first.");
      }
    } catch (error: any) {
      setStatus(`❌ Exception: ${error.message}`);
    }
  };

  const testSaveCondition = async () => {
    try {
      setStatus("Testing save condition...");
      const result = await ocrApi.addHealthCondition({
        condition_type: "illness",
        condition_name: "fever",
        severity: "moderate"
      });
      setStatus(`✅ Saved! ${JSON.stringify(result)}`);
    } catch (error: any) {
      setStatus(`❌ Save Error: ${error.message}`);
    }
  };

  const testGetConditions = async () => {
    try {
      setStatus("Fetching conditions...");
      const result = await ocrApi.getHealthConditions();
      setConditions(result);
      setStatus(`✅ Got ${result.length} conditions`);
    } catch (error: any) {
      setStatus(`❌ Get Error: ${error.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-2xl mx-auto bg-white rounded-lg shadow p-6">
        <h1 className="text-2xl font-bold mb-4">Health Conditions Diagnostic</h1>
        
        <div className="space-y-4">
          <button
            onClick={testAuth}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded hover:bg-blue-700"
          >
            1. Test Authentication
          </button>

          <button
            onClick={testSaveCondition}
            className="w-full bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700"
          >
            2. Test Save Condition
          </button>

          <button
            onClick={testGetConditions}
            className="w-full bg-purple-600 text-white py-2 px-4 rounded hover:bg-purple-700"
          >
            3. Test Get Conditions
          </button>

          <div className="mt-4 p-4 bg-gray-50 rounded">
            <h2 className="font-semibold mb-2">Status:</h2>
            <p className="text-sm">{status || "No status yet"}</p>
          </div>

          {token && (
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <h2 className="font-semibold mb-2">Token (first 50 chars):</h2>
              <p className="text-xs font-mono break-all">{token.substring(0, 50)}...</p>
            </div>
          )}

          {conditions.length > 0 && (
            <div className="mt-4 p-4 bg-gray-50 rounded">
              <h2 className="font-semibold mb-2">Conditions:</h2>
              <pre className="text-xs">{JSON.stringify(conditions, null, 2)}</pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

