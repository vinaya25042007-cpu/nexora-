import React, { useState } from "react";
import { UploadCloud, Sparkles, CheckCircle2, Circle, CalendarClock } from "lucide-react";

// generateRecoveryPlan() simulates the AI call that would parse a discharge
// summary into a structured plan. Swap the body of this function for a real
// request to your backend (which in turn calls the Claude API), e.g.:
//
//   const res = await fetch("/api/recovery-plan", {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify({ dischargeSummaryText }),
//   });
//   return await res.json();
//
async function generateRecoveryPlan(fileName) {
  await new Promise((r) => setTimeout(r, 1400)); // simulate processing time
  return {
    summary: `Parsed discharge summary "${fileName}". Plan generated for laparoscopic cholecystectomy recovery, day 0–21, tailored to a 58-year-old patient with no reported comorbidities.`,
  };
}

export default function RecoveryPlan({ plan, setPlan }) {
  const [fileName, setFileName] = useState(null);
  const [loading, setLoading] = useState(false);
  const [aiSummary, setAiSummary] = useState(null);

  const handleUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setFileName(file.name);
    setLoading(true);
    const result = await generateRecoveryPlan(file.name);
    setAiSummary(result.summary);
    setLoading(false);
  };

  const toggleRehab = (id) => {
    setPlan((prev) => ({
      ...prev,
      rehab: prev.rehab.map((r) => (r.id === id ? { ...r, done: !r.done } : r)),
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold">Recovery Plan</h1>
        <p className="text-ink/60 text-sm">Upload your discharge summary and let AI build your personalized plan.</p>
      </div>

      <div className="bg-white rounded-2xl p-6 border border-dashed border-teal/30 shadow-sm">
        <label className="flex flex-col items-center justify-center gap-2 cursor-pointer py-6 text-center">
          <UploadCloud className="w-8 h-8 text-teal" />
          <span className="font-medium text-sm">
            {fileName ? `Uploaded: ${fileName}` : "Click to upload discharge summary (PDF/image)"}
          </span>
          <span className="text-xs text-ink/50">AI extracts medications, instructions, and follow-up dates automatically</span>
          <input type="file" accept=".pdf,image/*" className="hidden" onChange={handleUpload} />
        </label>
        {loading && (
          <div className="flex items-center gap-2 text-sm text-teal justify-center mt-2">
            <Sparkles className="w-4 h-4 animate-pulse" /> Analyzing discharge summary…
          </div>
        )}
        {aiSummary && !loading && (
          <div className="mt-3 bg-sage-light text-teal text-sm rounded-xl p-3">{aiSummary}</div>
        )}
      </div>

      <div className="grid md:grid-cols-2 gap-5">
        <section className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <h2 className="font-display font-semibold mb-3">Rehabilitation exercises</h2>
          <ul className="space-y-2">
            {plan.rehab.map((r) => (
              <li key={r.id}>
                <button
                  onClick={() => toggleRehab(r.id)}
                  className="w-full flex items-start gap-3 text-left p-3 rounded-xl hover:bg-cream transition-colors"
                >
                  {r.done ? <CheckCircle2 className="w-5 h-5 text-sage shrink-0 mt-0.5" /> : <Circle className="w-5 h-5 text-ink/30 shrink-0 mt-0.5" />}
                  <div>
                    <p className={`text-sm font-medium ${r.done ? "line-through text-ink/40" : ""}`}>{r.title}</p>
                    <p className="text-xs text-ink/50">{r.frequency}</p>
                  </div>
                </button>
              </li>
            ))}
          </ul>
        </section>

        <section className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <h2 className="font-display font-semibold mb-3">Diet recommendations</h2>
          <ul className="space-y-2 text-sm">
            {plan.diet.map((d, i) => (
              <li key={i} className="flex items-start gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-amber mt-2 shrink-0" />
                <span>{d}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="bg-white rounded-2xl p-5 shadow-sm border border-black/5 md:col-span-2">
          <h2 className="font-display font-semibold mb-3 flex items-center gap-2">
            <CalendarClock className="w-5 h-5 text-teal" /> Upcoming follow-ups
          </h2>
          <div className="flex flex-wrap gap-3">
            {plan.followUps.map((f) => (
              <div key={f.id} className="bg-cream rounded-xl px-4 py-3 text-sm">
                <p className="font-medium">{f.label}</p>
                <p className="text-ink/50 text-xs">{f.date}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}