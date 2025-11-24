"use client";

import { useState, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";

// Initialize Supabase client
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

const getSupabaseClient = () => {
  if (!supabaseUrl || !supabaseKey) {
    console.warn("Supabase credentials not configured");
    return null;
  }
  return createClient(supabaseUrl, supabaseKey);
};

interface UserProfile {
  id: string;
  email: string;
  name?: string;
  avatar_url?: string;
  created_at: string;
  last_sign_in_at?: string;
}

export default function UserProfile() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const supabase = getSupabaseClient();

  useEffect(() => {
    getUserProfile();
  }, []);

  const getUserProfile = async () => {
    if (!supabase) {
      setMessage("Supabase not configured");
      setLoading(false);
      return;
    }

    try {
      const { data: { user }, error } = await supabase.auth.getUser();

      if (error) {
        throw error;
      }

      if (user) {
        setUser({
          id: user.id,
          email: user.email || "",
          name: user.user_metadata?.name || user.user_metadata?.full_name || "User",
          avatar_url: user.user_metadata?.avatar_url,
          created_at: user.created_at,
          last_sign_in_at: user.last_sign_in_at
        });
      }
    } catch (error: any) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSignOut = async () => {
    if (!supabase) return;

    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;

      // Redirect to home or reload page
      window.location.reload();
    } catch (error: any) {
      setMessage(error.message);
    }
  };

  if (loading) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-auto">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-3/4 mb-4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-auto">
        <p className="text-center text-gray-600">Please sign in to view your profile</p>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-auto">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 text-center">User Profile</h2>

      <div className="space-y-4">
        {/* Avatar */}
        <div className="flex justify-center">
          {user.avatar_url ? (
            <img
              src={user.avatar_url}
              alt="Profile"
              className="w-20 h-20 rounded-full object-cover"
            />
          ) : (
            <div className="w-20 h-20 bg-gray-300 rounded-full flex items-center justify-center">
              <span className="text-2xl text-gray-600 font-bold">
                {user.name?.charAt(0)?.toUpperCase() || user.email.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
        </div>

        {/* User Info */}
        <div className="space-y-3">
          <div>
            <label className="block text-sm font-medium text-gray-700">Name</label>
            <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded">{user.name}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded">{user.email}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">User ID</label>
            <p className="text-gray-500 bg-gray-50 px-3 py-2 rounded text-sm font-mono">{user.id}</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700">Member Since</label>
            <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded">
              {new Date(user.created_at).toLocaleDateString()}
            </p>
          </div>

          {user.last_sign_in_at && (
            <div>
              <label className="block text-sm font-medium text-gray-700">Last Sign In</label>
              <p className="text-gray-900 bg-gray-50 px-3 py-2 rounded">
                {new Date(user.last_sign_in_at).toLocaleString()}
              </p>
            </div>
          )}
        </div>

        {/* Sign Out Button */}
        <button
          onClick={handleSignOut}
          className="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-2 px-4 rounded-lg transition"
        >
          Sign Out
        </button>
      </div>

      {message && (
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
          {message}
        </div>
      )}
    </div>
  );
}