import React, { useState } from "react";
import { Camera, AlertTriangle, CheckCircle, AlertCircle, History } from "lucide-react";

// classifyWound() simulates the computer-vision model. Replace with a call to
// your backend endpoint that runs the actual CV model (or a Claude vision
// call) on the uploaded image, returning { risk, note }:
//
//   const res = await fetch("/api/wound-analysis", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ imageBase64 }),
//   });
//   return await res.json();
//
async function classifyWound() {
  await new Promise((r) => setTimeout(r, 1600));
  const outcomes = [
    { risk: "normal", note: "Incision edges are clean and well-approximated. No signs of infection." },
    { risk: "mild", note: "Slight redness around the incision border. Likely normal inflammation — monitor over 48 hours." },
    { risk: "urgent", note: "Increased swelling, spreading redness, and possible discharge detected. This pattern is consistent with a wound infection." },
  ];
  const weights = [0.6, 0.3, 0.1];
  const r = Math.random();
  const idx = r < weights[0] ? 0 : r < weights[0] + weights[1] ? 1 : 2;
  return outcomes[idx];
}

// Tailwind needs full, static class names (no string interpolation) to
// detect them at build time, so each risk level maps to a complete class string.
const RISK_META = {
  normal: { label: "Normal", classes: "bg-sage-light text-teal", icon: CheckCircle },
  mild: { label: "Mild Concern", classes: "bg-amber-light text-amber", icon: AlertCircle },
  urgent: { label: "Urgent", classes: "bg-coral-light text-coral", icon: AlertTriangle },
};

function RiskBadge({ risk }) {
  const { label, classes, icon: Icon } = RISK_META[risk];
  return (
    <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold ${classes}`}>
      <Icon className="w-3.5 h-3.5" /> {label}
    </span>
  );
}

export default function WoundScan({ history, setHistory, onUrgent }) {
  const [preview, setPreview] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState(null);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    setResult(null);
    setAnalyzing(true);
    const outcome = await classifyWound();
    setAnalyzing(false);
    setResult(outcome);
    const entry = { id: `w${Date.now()}`, date: new Date().toISOString().slice(0, 10), ...outcome };
    setHistory((prev) => [entry, ...prev]);
    if (outcome.risk === "urgent") onUrgent(entry);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold">Wound Scan</h1>
        <p className="text-ink/60 text-sm">Upload a photo of your incision. AI checks for signs of infection or poor healing.</p>
      </div>

      <div className="bg-white rounded-2xl p-6 shadow-sm border border-black/5 grid md:grid-cols-2 gap-6">
        <label className="flex flex-col items-center justify-center gap-2 cursor-pointer border-2 border-dashed border-teal/30 rounded-2xl py-10 px-4 text-center hover:bg-cream/50 transition-colors">
          {preview ? (
            <img src={preview} alt="Uploaded wound" className="max-h-48 rounded-xl object-cover" />
          ) : (
            <>
              <Camera className="w-8 h-8 text-teal" />
              <span className="font-medium text-sm">Take or upload a wound photo</span>
              <span className="text-xs text-ink/50">Good lighting, no flash glare, incision centered</span>
            </>
          )}
          <input type="file" accept="image/*" capture="environment" className="hidden" onChange={handleUpload} />
        </label>

        <div className="flex flex-col justify-center">
          {analyzing && (
            <div className="text-sm text-teal flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-teal animate-ping" /> Analyzing image for signs of infection…
            </div>
          )}
          {result && !analyzing && (
            <div className="space-y-3">
              <RiskBadge risk={result.risk} />
              <p className="text-sm text-ink/70">{result.note}</p>
              {result.risk === "urgent" && (
                <div className="bg-coral-light text-coral text-sm rounded-xl p-3 font-medium">
                  Your care team and caregiver have been alerted automatically.
                </div>
              )}
              <p className="text-xs text-ink/40">
                This is an AI screening tool, not a diagnosis. When in doubt, contact your surgeon.
              </p>
            </div>
          )}
          {!result && !analyzing && (
            <p className="text-sm text-ink/40">Your analysis will appear here after upload.</p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
        <h2 className="font-display font-semibold mb-3 flex items-center gap-2">
          <History className="w-5 h-5 text-teal" /> Scan history
        </h2>
        <div className="space-y-2">
          {history.map((h) => (
            <div key={h.id} className="flex items-center justify-between p-3 rounded-xl bg-cream/60">
              <div>
                <p className="text-sm font-medium">{h.date}</p>
                <p className="text-xs text-ink/50">{h.note}</p>
              </div>
              <RiskBadge risk={h.risk} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}