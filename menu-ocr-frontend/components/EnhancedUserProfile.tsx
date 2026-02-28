"use client";

import { useState, useEffect } from "react";
import { createClient } from "@supabase/supabase-js";

interface UserProfile {
  id: string;
  email: string;
  full_name?: string;
  phone?: string;
  address_street?: string;
  address_city?: string;
  address_state?: string;
  address_zip?: string;
  address_country?: string;
  subscription_plan?: string;
  referral_code?: string;
  referral_count?: number;
  created_at: string;
}

interface Address {
  id: string;
  type: string;
  street: string;
  apartment_number?: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  is_primary: boolean;
  created_at: string;
}

interface ReferralInfo {
  referral_code: string;
  referral_count: number;
  referral_link: string;
  pending_referrals: any[];
}

export default function EnhancedUserProfile() {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [addresses, setAddresses] = useState<Address[]>([]);
  const [referralInfo, setReferralInfo] = useState<ReferralInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'profile' | 'addresses' | 'password' | 'referral'>('profile');
  const [message, setMessage] = useState("");
  const supabase = getSupabaseClient();

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    if (!supabase) {
      setLoading(false);
      return;
    }

    try {
      const { data: { user } } = await supabase.auth.getUser();
      if (user) {
        await loadProfile();
        await loadAddresses();
        await loadReferralInfo();
      }
    } catch (error: any) {
      setMessage(error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadProfile = async () => {
    try {
      const token = await supabase!.auth.getSession();
      if (!token.data.session) return;

      const response = await fetch("/api/user/profile", {
        headers: {
          'Authorization': `Bearer ${token.data.session.access_token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUser(data.profile);
      }
    } catch (error) {
      console.error("Error loading profile:", error);
    }
  };

  const loadAddresses = async () => {
    try {
      const token = await supabase!.auth.getSession();
      if (!token.data.session) return;

      const response = await fetch("/api/user/addresses", {
        headers: {
          'Authorization': `Bearer ${token.data.session.access_token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAddresses(data);
      }
    } catch (error) {
      console.error("Error loading addresses:", error);
    }
  };

  const loadReferralInfo = async () => {
    try {
      const token = await supabase!.auth.getSession();
      if (!token.data.session) return;

      const response = await fetch("/api/user/referral", {
        headers: {
          'Authorization': `Bearer ${token.data.session.access_token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setReferralInfo(data);
      }
    } catch (error) {
      console.error("Error loading referral info:", error);
    }
  };

  const handleProfileUpdate = async (formData: any) => {
    try {
      setMessage("");
      const token = await supabase!.auth.getSession();
      if (!token.data.session) throw new Error("Not authenticated");

      const response = await fetch("/api/user/profile", {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token.data.session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (response.ok) {
        setMessage("Profile updated successfully!");
        await loadProfile();
      } else {
        throw new Error("Failed to update profile");
      }
    } catch (error: any) {
      setMessage(error.message || "Failed to update profile");
    }
  };

  const handlePasswordChange = async (currentPassword: string, newPassword: string) => {
    try {
      setMessage("");
      const token = await supabase!.auth.getSession();
      if (!token.data.session) throw new Error("Not authenticated");

      const response = await fetch("/api/user/change-password", {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token.data.session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          current_password: currentPassword,
          new_password: newPassword
        })
      });

      if (response.ok) {
        setMessage("Password changed successfully!");
      } else {
        const data = await response.json();
        throw new Error(data.detail || "Failed to change password");
      }
    } catch (error: any) {
      setMessage(error.message || "Failed to change password");
    }
  };

  const handleAddressSubmit = async (addressData: any) => {
    try {
      setMessage("");
      const token = await supabase!.auth.getSession();
      if (!token.data.session) throw new Error("Not authenticated");

      const response = await fetch("/api/user/addresses", {
        method: "POST",
        headers: {
          'Authorization': `Bearer ${token.data.session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(addressData)
      });

      if (response.ok) {
        setMessage("Address added successfully!");
        await loadAddresses();
      } else {
        throw new Error("Failed to add address");
      }
    } catch (error: any) {
      setMessage(error.message || "Failed to add address");
    }
  };

  const handleSignOut = async () => {
    if (!supabase) return;
    try {
      const { error } = await supabase.auth.signOut();
      if (!error) {
        window.location.reload();
      }
    } catch (error: any) {
      setMessage(error.message);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="animate-pulse">
            <div className="h-8 bg-gray-200 rounded w-1/3 mb-8"></div>
            <div className="bg-white p-8 rounded-lg shadow">
              <div className="h-4 bg-gray-200 rounded w-1/2 mb-4"></div>
              <div className="h-4 bg-gray-200 rounded w-2/3"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-gray-600">Please sign in to view your profile</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow overflow-hidden">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200">
            <h1 className="text-2xl font-bold text-gray-900">Account Settings</h1>
            <p className="text-gray-600">Manage your profile and preferences</p>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {[
                { id: 'profile', label: 'Profile' },
                { id: 'addresses', label: 'Addresses' },
                { id: 'password', label: 'Password' },
                { id: 'referral', label: 'Referral' }
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'profile' && (
              <ProfileTab user={user} onUpdate={handleProfileUpdate} />
            )}
            {activeTab === 'addresses' && (
              <AddressesTab addresses={addresses} onSubmit={handleAddressSubmit} />
            )}
            {activeTab === 'password' && (
              <PasswordTab onChange={handlePasswordChange} />
            )}
            {activeTab === 'referral' && (
              <ReferralTab referralInfo={referralInfo} />
            )}
          </div>
        </div>

        {/* Sign Out */}
        <div className="mt-6">
          <button
            onClick={handleSignOut}
            className="w-full bg-red-600 text-white py-2 px-4 rounded-lg hover:bg-red-700 transition"
          >
            Sign Out
          </button>
        </div>

        {/* Message Display */}
        {message && (
          <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
            {message}
          </div>
        )}
      </div>
    </div>
  );
}

// Profile Tab Component
function ProfileTab({ user, onUpdate }: { user: UserProfile; onUpdate: (data: any) => void }) {
  const [formData, setFormData] = useState({
    full_name: user.full_name || '',
    phone: user.phone || '',
    address_street: user.address_street || '',
    address_city: user.address_city || '',
    address_state: user.address_state || '',
    address_zip: user.address_zip || '',
    address_country: user.address_country || 'US'
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onUpdate(formData);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700">Full Name</label>
          <input
            type="text"
            value={formData.full_name}
            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Phone</label>
          <input
            type="tel"
            value={formData.phone}
            onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
            className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">Address</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="md:col-span-2">
            <label className="block text-sm font-medium text-gray-700">Street Address</label>
            <input
              type="text"
              value={formData.address_street}
              onChange={(e) => setFormData({ ...formData, address_street: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">City</label>
            <input
              type="text"
              value={formData.address_city}
              onChange={(e) => setFormData({ ...formData, address_city: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">State</label>
            <input
              type="text"
              value={formData.address_state}
              onChange={(e) => setFormData({ ...formData, address_state: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">ZIP Code</label>
            <input
              type="text"
              value={formData.address_zip}
              onChange={(e) => setFormData({ ...formData, address_zip: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Country</label>
            <select
              value={formData.address_country}
              onChange={(e) => setFormData({ ...formData, address_country: e.target.value })}
              className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="US">United States</option>
              <option value="CA">Canada</option>
            </select>
          </div>
        </div>
      </div>

      <button
        type="submit"
        className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
      >
        Update Profile
      </button>
    </form>
  );
}

// Addresses Tab Component
function AddressesTab({ addresses, onSubmit }: { addresses: Address[]; onSubmit: (data: any) => void }) {
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    type: 'home',
    street: '',
    apartment_number: '',
    city: '',
    state: '',
    zip_code: '',
    country: 'US',
    is_primary: false
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(formData);
    setFormData({
      type: 'home',
      street: '',
      apartment_number: '',
      city: '',
      state: '',
      zip_code: '',
      country: 'US',
      is_primary: false
    });
    setShowForm(false);
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-medium text-gray-900">Your Addresses</h3>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
        >
          Add Address
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-50 p-4 rounded-lg mb-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Type</label>
              <select
                value={formData.type}
                onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md"
              >
                <option value="home">Home</option>
                <option value="work">Work</option>
                <option value="delivery">Delivery</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Primary Address?</label>
              <input
                type="checkbox"
                checked={formData.is_primary}
                onChange={(e) => setFormData({ ...formData, is_primary: e.target.checked })}
                className="mt-1"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">Street</label>
              <input
                type="text"
                required
                value={formData.street}
                onChange={(e) => setFormData({ ...formData, street: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md"
              />
            </div>
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">Apartment/Unit</label>
              <input
                type="text"
                value={formData.apartment_number}
                onChange={(e) => setFormData({ ...formData, apartment_number: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">City</label>
              <input
                type="text"
                required
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">State</label>
              <input
                type="text"
                required
                value={formData.state}
                onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">ZIP Code</label>
              <input
                type="text"
                required
                value={formData.zip_code}
                onChange={(e) => setFormData({ ...formData, zip_code: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Country</label>
              <select
                value={formData.country}
                onChange={(e) => setFormData({ ...formData, country: e.target.value })}
                className="mt-1 block w-full border-gray-300 rounded-md"
              >
                <option value="US">United States</option>
                <option value="CA">Canada</option>
              </select>
            </div>
          </div>
          <div className="mt-4 flex space-x-4">
            <button
              type="submit"
              className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition"
            >
              Save Address
            </button>
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="space-y-4">
        {addresses.length === 0 ? (
          <p className="text-gray-500 text-center py-8">No addresses added yet.</p>
        ) : (
          addresses.map((address) => (
            <div key={address.id} className="border border-gray-200 p-4 rounded-lg">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium text-gray-900 capitalize">{address.type}</h4>
                  <p className="text-gray-600">{address.street}</p>
                  {address.apartment_number && (
                    <p className="text-gray-600">Apt {address.apartment_number}</p>
                  )}
                  <p className="text-gray-600">
                    {address.city}, {address.state} {address.zip_code}
                  </p>
                  <p className="text-gray-600">{address.country}</p>
                  {address.is_primary && (
                    <span className="inline-block mt-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded">
                      Primary
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// Password Tab Component
function PasswordTab({ onChange }: { onChange: (current: string, newPassword: string) => void }) {
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (newPassword !== confirmPassword) {
      alert("Passwords don't match!");
      return;
    }
    if (newPassword.length < 8) {
      alert("Password must be at least 8 characters!");
      return;
    }
    onChange(currentPassword, newPassword);
    setCurrentPassword('');
    setNewPassword('');
    setConfirmPassword('');
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-md">
      <div>
        <label className="block text-sm font-medium text-gray-700">Current Password</label>
        <input
          type="password"
          required
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">New Password</label>
        <input
          type="password"
          required
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        />
        <p className="text-sm text-gray-500 mt-1">Must be at least 8 characters</p>
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700">Confirm New Password</label>
        <input
          type="password"
          required
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <button
        type="submit"
        className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition"
      >
        Change Password
      </button>
    </form>
  );
}

// Referral Tab Component
function ReferralTab({ referralInfo }: { referralInfo: ReferralInfo | null }) {
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('Copied to clipboard!');
  };

  if (!referralInfo) return null;

  return (
    <div className="space-y-6">
      <div className="bg-blue-50 p-6 rounded-lg">
        <h3 className="text-lg font-medium text-blue-900 mb-4">Referral Program</h3>
        <p className="text-blue-700 mb-4">
          Share your referral code and earn rewards! You get 1 month free for each friend who subscribes.
        </p>

        <div className="bg-white p-4 rounded border">
          <label className="block text-sm font-medium text-gray-700 mb-2">Your Referral Code</label>
          <div className="flex items-center space-x-2">
            <code className="flex-1 bg-gray-100 px-3 py-2 rounded font-mono">
              {referralInfo.referral_code}
            </code>
            <button
              onClick={() => copyToClipboard(referralInfo.referral_code)}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
            >
              Copy
            </button>
          </div>
        </div>

        <div className="mt-4 bg-white p-4 rounded border">
          <label className="block text-sm font-medium text-gray-700 mb-2">Your Referral Link</label>
          <div className="flex items-center space-x-2">
            <code className="flex-1 bg-gray-100 px-3 py-2 rounded text-sm">
              {referralInfo.referral_link}
            </code>
            <button
              onClick={() => copyToClipboard(referralInfo.referral_link)}
              className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
            >
              Copy
            </button>
          </div>
        </div>

        <div className="mt-4">
          <p className="text-blue-700">
            <strong>{referralInfo.referral_count}</strong> successful referrals
          </p>
        </div>
      </div>
    </div>
  );
}

// Helper function
function getSupabaseClient() {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";

  if (!supabaseUrl || !supabaseKey) {
    console.warn("Supabase credentials not configured");
    return null;
  }

  return createClient(supabaseUrl, supabaseKey);
}