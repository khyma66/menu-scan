import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Check, Plus, X, Save, ChevronDown, ChevronUp, Info } from "lucide-react";

const DIETARY_OPTIONS = ["Vegetarian", "Vegan", "Keto", "Gluten-Free", "Paleo", "Low-Sodium", "Halal", "Kosher"];
const TASTE_OPTIONS = ["Spicy 🌶️", "Mild", "Sweet", "Tangy", "Savory", "Sour", "Umami", "Bitter"];
const COMMON_ALLERGIES = ["Peanuts", "Tree Nuts", "Dairy", "Eggs", "Gluten", "Shellfish", "Soy", "Fish"];
const HEALTH_CONDITIONS = ["Diabetes", "Hypertension", "Heart Disease", "Celiac", "IBS", "High Cholesterol", "Obesity", "Gout"];

function Section({
  emoji,
  title,
  subtitle,
  children,
  defaultOpen = true,
}: {
  emoji: string;
  title: string;
  subtitle: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-2xl shadow-sm overflow-hidden"
    >
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4"
      >
        <div className="flex items-center gap-3">
          <div className="text-xl">{emoji}</div>
          <div className="text-left">
            <div className="font-bold text-gray-800 text-sm">{title}</div>
            <div className="text-xs text-gray-400">{subtitle}</div>
          </div>
        </div>
        <motion.div animate={{ rotate: open ? 180 : 0 }} transition={{ duration: 0.2 }}>
          <ChevronDown size={18} className="text-gray-400" />
        </motion.div>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-4 pb-4">{children}</div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}

function ChipSelector({
  options,
  selected,
  onToggle,
  activeColor = "#3B5BDB",
}: {
  options: string[];
  selected: string[];
  onToggle: (v: string) => void;
  activeColor?: string;
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map(opt => {
        const active = selected.includes(opt);
        return (
          <motion.button
            key={opt}
            whileTap={{ scale: 0.92 }}
            onClick={() => onToggle(opt)}
            className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-medium transition-all"
            style={{
              backgroundColor: active ? activeColor + "18" : "#F3F4F6",
              color: active ? activeColor : "#6B7280",
              border: `1.5px solid ${active ? activeColor : "transparent"}`,
            }}
          >
            <motion.div
              animate={active ? { scale: [0.8, 1.2, 1], rotate: [0, 10, 0] } : { scale: 0 }}
              transition={{ duration: 0.3 }}
              className={active ? "block" : "hidden"}
            >
              <Check size={11} />
            </motion.div>
            {opt}
          </motion.button>
        );
      })}
    </div>
  );
}

function TagInput({
  value,
  onChange,
  placeholder,
  suggestions,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
  suggestions: string[];
}) {
  const [tags, setTags] = useState<string[]>([]);
  const [input, setInput] = useState("");
  const [focused, setFocused] = useState(false);

  const addTag = (tag: string) => {
    const trimmed = tag.trim();
    if (trimmed && !tags.includes(trimmed)) {
      setTags(prev => [...prev, trimmed]);
    }
    setInput("");
  };

  const removeTag = (tag: string) => {
    setTags(prev => prev.filter(t => t !== tag));
  };

  return (
    <div>
      <motion.div
        animate={{
          borderColor: focused ? "#3B5BDB" : "#E5E7EB",
          boxShadow: focused ? "0 0 0 3px rgba(59,91,219,0.1)" : "none",
        }}
        className="flex flex-wrap gap-1.5 p-2.5 rounded-xl border-2 bg-gray-50 min-h-[46px]"
      >
        <AnimatePresence>
          {tags.map(tag => (
            <motion.span
              key={tag}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0, opacity: 0 }}
              className="flex items-center gap-1 px-2.5 py-1 bg-blue-100 text-blue-700 rounded-lg text-xs font-medium"
            >
              {tag}
              <button onClick={() => removeTag(tag)}>
                <X size={11} />
              </button>
            </motion.span>
          ))}
        </AnimatePresence>
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          onFocus={() => setFocused(true)}
          onBlur={() => { setFocused(false); if (input.trim()) addTag(input); }}
          onKeyDown={e => {
            if ((e.key === "Enter" || e.key === ",") && input.trim()) {
              e.preventDefault();
              addTag(input);
            }
            if (e.key === "Backspace" && !input && tags.length) {
              removeTag(tags[tags.length - 1]);
            }
          }}
          placeholder={tags.length ? "" : placeholder}
          className="flex-1 min-w-[120px] bg-transparent outline-none text-sm text-gray-700 placeholder:text-gray-400"
        />
      </motion.div>
      {/* Quick suggestions */}
      <div className="flex gap-1.5 mt-2 overflow-x-auto pb-0.5 scrollbar-none">
        {suggestions.filter(s => !tags.includes(s)).slice(0, 5).map(s => (
          <button
            key={s}
            onClick={() => addTag(s)}
            className="flex items-center gap-1 px-2.5 py-1 bg-gray-100 rounded-lg text-xs text-gray-600 whitespace-nowrap flex-shrink-0 hover:bg-blue-50 hover:text-blue-600 transition-colors"
          >
            <Plus size={10} />
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}

export function HealthPlus() {
  const [dietary, setDietary] = useState<string[]>([]);
  const [tastes, setTastes] = useState<string[]>([]);
  const [allergies, setAllergies] = useState<string[]>([]);
  const [conditions, setConditions] = useState<string[]>([]);
  const [medicalNotes, setMedicalNotes] = useState("");
  const [saved, setSaved] = useState(false);

  const toggleItem = (list: string[], setList: (v: string[]) => void, item: string) => {
    setList(list.includes(item) ? list.filter(i => i !== item) : [...list, item]);
  };

  const handleSave = () => {
    setSaved(true);
    setTimeout(() => setSaved(false), 2500);
  };

  const totalSelections = dietary.length + tastes.length + allergies.length + conditions.length;

  return (
    <div className="flex flex-col min-h-full bg-gray-50">
      {/* Header */}
      <div
        className="relative px-5 pt-7 pb-5 overflow-hidden"
        style={{ backgroundColor: "#059669" }}
      >
        <div className="absolute -top-8 -right-8 w-32 h-32 rounded-full bg-white/10" />
        <div className="absolute -bottom-6 -left-6 w-24 h-24 rounded-full bg-white/10" />

        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center"
        >
          <motion.div
            animate={{
              scale: [1, 1.12, 0.95, 1.08, 1],
            }}
            transition={{ duration: 1.5, repeat: Infinity, repeatDelay: 3 }}
            className="text-2xl mb-1.5"
          >
            💚
          </motion.div>
          <h1 className="text-white mb-1" style={{ fontWeight: 800, fontSize: "22px" }}>Health Profile</h1>
          <p className="text-white/80 text-xs px-4 text-center">
            Set preferences once and get safer dish recommendations instantly
          </p>
        </motion.div>

        {/* Progress pill */}
        {totalSelections > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            className="mt-4 mx-auto w-fit px-4 py-1.5 bg-white/20 backdrop-blur rounded-full"
          >
            <span className="text-white text-xs font-medium">{totalSelections} preferences set ✓</span>
          </motion.div>
        )}
      </div>

      {/* Info banner */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="mx-4 -mt-3 bg-blue-50 border border-blue-100 rounded-xl p-3 flex gap-2 items-start"
      >
        <Info size={16} className="text-blue-500 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-blue-700">
          Your health data stays on your device. We use it to filter menu suggestions in real time.
        </p>
      </motion.div>

      {/* Sections */}
      <div className="px-4 mt-4 space-y-3 pb-24">

        <Section emoji="🩺" title="Health Conditions" subtitle="e.g., diabetes, hypertension, heart disease">
          <ChipSelector
            options={HEALTH_CONDITIONS}
            selected={conditions}
            onToggle={v => toggleItem(conditions, setConditions, v)}
            activeColor="#EF4444"
          />
          <div className="mt-3">
            <TagInput
              value=""
              onChange={() => {}}
              placeholder="Add custom condition..."
              suggestions={[]}
            />
          </div>
        </Section>

        <Section emoji="🚫" title="Allergies" subtitle="e.g., peanuts, shellfish, dairy, gluten">
          <ChipSelector
            options={COMMON_ALLERGIES}
            selected={allergies}
            onToggle={v => toggleItem(allergies, setAllergies, v)}
            activeColor="#F97316"
          />
          <div className="mt-3">
            <TagInput
              value=""
              onChange={() => {}}
              placeholder="Add custom allergy..."
              suggestions={[]}
            />
          </div>
        </Section>

        <Section emoji="🥗" title="Dietary Preferences" subtitle="e.g., vegetarian, vegan, keto, low-sodium">
          <ChipSelector
            options={DIETARY_OPTIONS}
            selected={dietary}
            onToggle={v => toggleItem(dietary, setDietary, v)}
            activeColor="#22C55E"
          />
        </Section>

        <Section emoji="👅" title="Taste Preferences" subtitle="e.g., spicy, mild, sweet, tangy, savory">
          <ChipSelector
            options={TASTE_OPTIONS}
            selected={tastes}
            onToggle={v => toggleItem(tastes, setTastes, v)}
            activeColor="#8B5CF6"
          />
        </Section>

        <Section emoji="📝" title="Medical Notes" subtitle="Any additional notes for your health advisor" defaultOpen={false}>
          <motion.textarea
            whileFocus={{ borderColor: "#3B5BDB", boxShadow: "0 0 0 3px rgba(59,91,219,0.1)" }}
            value={medicalNotes}
            onChange={e => setMedicalNotes(e.target.value)}
            placeholder="Add any special medical instructions, medication interactions, or other relevant notes..."
            rows={4}
            className="w-full p-3 bg-gray-50 rounded-xl border-2 border-gray-200 outline-none text-sm text-gray-700 placeholder:text-gray-400 resize-none transition-all"
          />
          <div className="text-right text-xs text-gray-400 mt-1">{medicalNotes.length}/500</div>
        </Section>

        {/* Save Button */}
        <motion.button
          whileTap={{ scale: 0.96 }}
          onClick={handleSave}
          className="w-full py-4 rounded-2xl font-bold text-white relative overflow-hidden"
          style={{
            background: saved
              ? "linear-gradient(135deg, #22C55E, #16A34A)"
              : "linear-gradient(135deg, #3B5BDB, #2563EB)",
          }}
          animate={{ background: saved ? ["#22C55E", "#22C55E"] : ["#3B5BDB", "#3B5BDB"] }}
        >
          <motion.div
            className="absolute inset-0 bg-white/20"
            initial={{ x: "-100%" }}
            animate={saved ? { x: "100%" } : {}}
            transition={{ duration: 0.5 }}
          />
          <AnimatePresence mode="wait">
            {saved ? (
              <motion.div
                key="saved"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="flex items-center justify-center gap-2"
              >
                <Check size={18} />
                Profile Saved!
              </motion.div>
            ) : (
              <motion.div
                key="save"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="flex items-center justify-center gap-2"
              >
                <Save size={18} />
                Save Health Profile
              </motion.div>
            )}
          </AnimatePresence>
        </motion.button>
      </div>
    </div>
  );
}