import React from "react";
import { Pill, CheckCircle2, Circle } from "lucide-react";

export default function Medications({ plan, setPlan }) {
  const toggleDose = (medId, doseIdx) => {
    setPlan((prev) => ({
      ...prev,
      medications: prev.medications.map((m) =>
        m.id === medId
          ? { ...m, taken: m.taken.map((t, i) => (i === doseIdx ? !t : t)) }
          : m
      ),
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold">Medications</h1>
        <p className="text-ink/60 text-sm">Track today's doses. Missed doses trigger a reminder and a caregiver nudge.</p>
      </div>

      <div className="space-y-4">
        {plan.medications.map((m) => {
          const adherence = Math.round((m.taken.filter(Boolean).length / m.taken.length) * 100);
          return (
            <div key={m.id} className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-xl bg-sage-light text-teal flex items-center justify-center shrink-0">
                    <Pill className="w-5 h-5" />
                  </div>
                  <div>
                    <p className="font-medium text-sm">{m.name}</p>
                    <p className="text-xs text-ink/50">{m.schedule} · {m.purpose}</p>
                  </div>
                </div>
                <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                  adherence >= 80 ? "bg-sage-light text-teal" : "bg-amber-light text-amber"
                }`}>
                  {adherence}% today
                </span>
              </div>

              <div className="flex gap-2 mt-4 flex-wrap">
                {m.taken.map((t, i) => (
                  <button
                    key={i}
                    onClick={() => toggleDose(m.id, i)}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                      t ? "bg-sage-light text-teal" : "bg-cream text-ink/50 hover:bg-black/5"
                    }`}
                  >
                    {t ? <CheckCircle2 className="w-3.5 h-3.5" /> : <Circle className="w-3.5 h-3.5" />}
                    Dose {i + 1}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}