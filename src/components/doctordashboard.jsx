import React from "react";
import { Stethoscope, AlertTriangle, CheckCircle, AlertCircle, FileText } from "lucide-react";

const RISK_META = {
  normal: { label: "Normal", classes: "bg-sage-light text-teal", icon: CheckCircle },
  mild: { label: "Mild Concern", classes: "bg-amber-light text-amber", icon: AlertCircle },
  urgent: { label: "Urgent", classes: "bg-coral-light text-coral", icon: AlertTriangle },
};

export default function DoctorDashboard({ patient, plan, woundHistory, alerts }) {
  const medAdherence = Math.round(
    (plan.medications.reduce((sum, m) => sum + m.taken.filter(Boolean).length, 0) /
      plan.medications.reduce((sum, m) => sum + m.taken.length, 0)) * 100
  );
  const rehabAdherence = Math.round(
    (plan.rehab.filter((r) => r.done).length / plan.rehab.length) * 100
  );
  const latestScan = woundHistory[0];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold flex items-center gap-2">
          <Stethoscope className="w-6 h-6 text-teal" /> Doctor View
        </h1>
        <p className="text-ink/60 text-sm">Remote monitoring summary — {patient.name}, Day {patient.recoveryDay} post-op.</p>
      </div>

      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <p className="text-xs text-ink/50">Medication adherence</p>
          <p className="font-display text-3xl font-semibold text-teal">{medAdherence}%</p>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <p className="text-xs text-ink/50">Rehab adherence</p>
          <p className="font-display text-3xl font-semibold text-teal">{rehabAdherence}%</p>
        </div>
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
          <p className="text-xs text-ink/50">Latest wound status</p>
          {latestScan ? (
            <span className={`inline-flex items-center gap-1.5 mt-1 px-3 py-1 rounded-full text-xs font-semibold ${RISK_META[latestScan.risk].classes}`}>
              {RISK_META[latestScan.risk].label}
            </span>
          ) : (
            <p className="text-sm text-ink/40">No scans yet</p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
        <h2 className="font-display font-semibold mb-3 flex items-center gap-2">
          <FileText className="w-5 h-5 text-teal" /> Wound progression
        </h2>
        <div className="space-y-2">
          {woundHistory.map((h) => {
            const meta = RISK_META[h.risk];
            const Icon = meta.icon;
            return (
              <div key={h.id} className="flex items-center justify-between p-3 rounded-xl bg-cream/60">
                <div className="flex items-center gap-3">
                  <Icon className="w-4 h-4" />
                  <div>
                    <p className="text-sm font-medium">{h.date}</p>
                    <p className="text-xs text-ink/50">{h.note}</p>
                  </div>
                </div>
                <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${meta.classes}`}>{meta.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
        <h2 className="font-display font-semibold mb-3">Care team alerts</h2>
        <div className="space-y-2">
          {alerts.length === 0 && <p className="text-sm text-ink/50">No active alerts for this patient.</p>}
          {alerts.map((a) => (
            <div key={a.id} className={`p-3 rounded-xl text-sm ${
              a.severity === "urgent" ? "bg-coral-light text-coral" : a.severity === "warning" ? "bg-amber-light text-amber" : "bg-sage-light text-teal"
            }`}>
              <p className="font-medium">{a.title}</p>
              <p className="text-xs opacity-80">{a.message} · {a.time}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}