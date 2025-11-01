"use client";

import { useState } from "react";

interface HealthCondition {
  condition_type: string;
  condition_name: string;
  severity?: string;
}

interface HealthConditionFormProps {
  onSubmit: (conditions: HealthCondition[]) => void;
  onCancel?: () => void;
}

export default function HealthConditionForm({ onSubmit, onCancel }: HealthConditionFormProps) {
  const [conditions, setConditions] = useState<HealthCondition[]>([]);
  const [conditionType, setConditionType] = useState<string>("allergy");
  const [conditionName, setConditionName] = useState<string>("");
  const [severity, setSeverity] = useState<string>("moderate");

  const conditionOptions = {
    allergy: ["peanut", "shellfish", "dairy", "egg", "nuts", "soy", "wheat"],
    illness: ["cough", "flu", "cold", "nausea", "indigestion", "constipation"],
    dietary: ["vegetarian", "vegan", "gluten-free", "keto", "halal", "kosher"],
  };

  const addCondition = () => {
    if (conditionName.trim()) {
      setConditions([
        ...conditions,
        {
          condition_type: conditionType,
          condition_name: conditionName,
          severity: conditionType === "illness" ? severity : undefined,
        },
      ]);
      setConditionName("");
    }
  };

  const removeCondition = (index: number) => {
    setConditions(conditions.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(conditions);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <h3 className="text-xl font-semibold text-gray-800 mb-4">Health Conditions</h3>

      {/* Condition Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Type
        </label>
        <div className="grid grid-cols-3 gap-2">
          <button
            type="button"
            onClick={() => setConditionType("allergy")}
            className={`px-4 py-2 rounded-lg transition ${
              conditionType === "allergy"
                ? "bg-blue-600 text-white"
                : "bg-gray-100 text-gray-700"
            }`}
          >
            Allergy
          </button>
          <button
            type="button"
            onClick={() => setConditionType("illness")}
            className={`px-4 py-2 rounded-lg transition ${
              conditionType === "illness"
                ? "bg-red-600 text-white"
                : "bg-gray-100 text-gray-700"
            }`}
          >
            Illness
          </button>
          <button
            type="button"
            onClick={() => setConditionType("dietary")}
            className={`px-4 py-2 rounded-lg transition ${
              conditionType === "dietary"
                ? "bg-green-600 text-white"
                : "bg-gray-100 text-gray-700"
            }`}
          >
            Dietary
          </button>
        </div>
      </div>

      {/* Condition Select */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Condition
        </label>
        <select
          value={conditionName}
          onChange={(e) => setConditionName(e.target.value)}
          className="w-full px-4 py-2 border border-gray-300 rounded-lg"
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
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Severity
          </label>
          <select
            value={severity}
            onChange={(e) => setSeverity(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg"
          >
            <option value="mild">Mild</option>
            <option value="moderate">Moderate</option>
            <option value="severe">Severe</option>
          </select>
        </div>
      )}

      {/* Add Button */}
      <button
        type="button"
        onClick={addCondition}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition"
      >
        Add Condition
      </button>

      {/* List of added conditions */}
      {conditions.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-gray-700">Added Conditions:</p>
          {conditions.map((cond, index) => (
            <div
              key={index}
              className="flex items-center justify-between bg-gray-50 p-3 rounded-lg"
            >
              <div>
                <span className="font-medium text-gray-800 capitalize">
                  {cond.condition_name}
                </span>
                <span className="text-sm text-gray-500 ml-2">
                  ({cond.condition_type})
                  {cond.severity && ` - ${cond.severity}`}
                </span>
              </div>
              <button
                type="button"
                onClick={() => removeCondition(index)}
                className="text-red-600 hover:text-red-700"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Submit and Cancel */}
      <div className="flex gap-2">
        <button
          type="submit"
          disabled={conditions.length === 0}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2 px-4 rounded-lg transition disabled:opacity-50"
        >
          Save Conditions
        </button>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 bg-gray-300 hover:bg-gray-400 text-gray-800 font-medium py-2 px-4 rounded-lg transition"
          >
            Skip
          </button>
        )}
      </div>
    </form>
  );
}

