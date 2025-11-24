"use client";

import { useState, useEffect } from "react";
import { newHealthAPI, type HealthCondition, type HealthProfile } from "@/lib/new-health-api";

interface NewHealthConditionFormProps {
  onSubmit?: (conditions: HealthCondition[]) => void;
  onCancel?: () => void;
}

export default function NewHealthConditionForm({ onSubmit, onCancel }: NewHealthConditionFormProps) {
  const [conditions, setConditions] = useState<HealthCondition[]>([]);
  const [conditionType, setConditionType] = useState<string>("allergy");
  const [conditionName, setConditionName] = useState<string>("");
  const [severity, setSeverity] = useState<string>("moderate");
  const [description, setDescription] = useState<string>("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");
  const [profile, setProfile] = useState<HealthProfile | null>(null);

  // Load existing profile and conditions on mount
  useEffect(() => {
    loadHealthProfile();
  }, []);

  const loadHealthProfile = async () => {
    try {
      setIsLoading(true);
      const profileData = await newHealthAPI.getProfile();
      setProfile(profileData);
      // Convert existing conditions to local state
      setConditions(profileData.conditions || []);
    } catch (error) {
      console.warn("No existing health profile found, will create one when adding conditions");
    } finally {
      setIsLoading(false);
    }
  };

  const conditionOptions = {
    allergy: ["peanut", "shellfish", "dairy", "egg", "nuts", "soy", "wheat", "gluten"],
    illness: ["fever", "flu", "cold", "cough", "gastrointestinal", "nausea", "indigestion", "stomach", "headache"],
    dietary: ["vegetarian", "vegan", "gluten-free", "keto", "halal", "kosher", "low-sodium", "diabetic"],
    preference: ["spicy", "mild", "organic", "low-calorie", "high-protein"]
  };

  const addCondition = () => {
    if (!conditionName.trim()) {
      setError("Please select a condition from the dropdown.");
      return;
    }

    const newCondition: HealthCondition = {
      condition_type: conditionType,
      condition_name: conditionName.trim(),
      severity: conditionType === "illness" ? severity : undefined,
      description: description.trim() || undefined
    };

    // Check for duplicates
    const isDuplicate = conditions.some(c =>
      c.condition_name.toLowerCase() === newCondition.condition_name.toLowerCase()
    );

    if (isDuplicate) {
      setError(`Condition "${conditionName}" is already added.`);
      return;
    }

    setConditions(prev => [...prev, newCondition]);
    setConditionName("");
    setDescription("");
    setError("");
  };

  const removeCondition = (index: number) => {
    setConditions(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (conditions.length === 0) {
      setError("Please add at least one health condition before saving.");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      console.log("💾 Saving health conditions:", conditions);

      // Add conditions one by one for better error handling
      const results = await newHealthAPI.addConditions(conditions);

      if (results.errors.length > 0) {
        setError(`Failed to save ${results.errors.length} condition(s): ${results.errors.map(e => e.condition).join(", ")}`);
        return;
      }

      console.log("✅ Successfully saved health conditions");
      onSubmit?.(conditions);

    } catch (error: any) {
      console.error("❌ Error saving health conditions:", error);
      setError(error.message || "Failed to save health conditions. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !profile) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">Loading health profile...</span>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">Health Conditions</h3>

        {profile && (
          <div className="mb-4 p-3 bg-blue-50 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Profile:</strong> {profile.profile_name || "Default Profile"}
              {profile.conditions.length > 0 && (
                <span className="ml-2">({profile.conditions.length} existing condition{profile.conditions.length !== 1 ? 's' : ''})</span>
              )}
            </p>
          </div>
        )}

        {/* Condition Type */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Type
          </label>
          <div className="grid grid-cols-2 gap-2">
            {Object.keys(conditionOptions).map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setConditionType(type)}
                className={`px-4 py-2 rounded-lg transition capitalize ${
                  conditionType === type
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {type}
              </button>
            ))}
          </div>
        </div>

        {/* Condition Select */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Condition
          </label>
          <select
            value={conditionName}
            onChange={(e) => setConditionName(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="">Choose a condition...</option>
            {conditionOptions[conditionType as keyof typeof conditionOptions]?.map((option) => (
              <option key={option} value={option}>
                {option.charAt(0).toUpperCase() + option.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Severity for illness */}
        {conditionType === "illness" && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Severity
            </label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="mild">Mild</option>
              <option value="moderate">Moderate</option>
              <option value="severe">Severe</option>
            </select>
          </div>
        )}

        {/* Description */}
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Description (Optional)
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Additional details about this condition..."
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            rows={2}
          />
        </div>

        {/* Add Button */}
        <button
          type="button"
          onClick={addCondition}
          disabled={!conditionName.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition disabled:cursor-not-allowed"
        >
          Add Condition
        </button>

        {/* Error Display */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        {/* List of added conditions */}
        {conditions.length > 0 && (
          <div className="mt-6 space-y-3">
            <p className="text-sm font-medium text-gray-700">Added Conditions:</p>
            {conditions.map((cond, index) => (
              <div
                key={index}
                className="flex items-center justify-between bg-gray-50 p-3 rounded-lg border"
              >
                <div className="flex-1">
                  <span className="font-medium text-gray-800 capitalize">
                    {cond.condition_name}
                  </span>
                  <span className="text-sm text-gray-500 ml-2">
                    ({cond.condition_type})
                    {cond.severity && ` - ${cond.severity}`}
                  </span>
                  {cond.description && (
                    <p className="text-sm text-gray-600 mt-1">{cond.description}</p>
                  )}
                </div>
                <button
                  type="button"
                  onClick={() => removeCondition(index)}
                  className="text-red-600 hover:text-red-700 ml-3"
                  title="Remove condition"
                >
                  ✕
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Submit and Cancel */}
        <div className="flex gap-3 mt-6">
          <button
            type="submit"
            disabled={conditions.length === 0 || isLoading}
            className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-lg transition disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                Saving...
              </span>
            ) : (
              `Save ${conditions.length} Condition${conditions.length !== 1 ? 's' : ''}`
            )}
          </button>
          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={isLoading}
              className="flex-1 bg-gray-300 hover:bg-gray-400 disabled:bg-gray-200 text-gray-800 font-medium py-2 px-4 rounded-lg transition disabled:cursor-not-allowed"
            >
              Skip
            </button>
          )}
        </div>
      </div>
    </form>
  );
}