import React from "react";
import { Bell, ThermometerSun, Frown, Utensils, TrendingUp } from "lucide-react";

// Signature element: a circular "healing ring" showing progress through the
// recovery window (day X of Y), color-shifting from amber → sage as it fills.
function HealingRing({ day, total }) {
  const pct = Math.min(day / total, 1);
  const radius = 70;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct);
  const color = pct < 0.34 ? "#E8A33D" : pct < 0.7 ? "#6FA98A" : "#12484B";

  return (
    <div className="relative w-44 h-44 shrink-0">
      <svg viewBox="0 0 160 160" className="w-full h-full -rotate-90">
        <circle cx="80" cy="80" r={radius} fill="none" stroke="#DCEBE2" strokeWidth="12" />
        <circle
          cx="80" cy="80" r={radius} fill="none" stroke={color} strokeWidth="12"
          strokeDasharray={circumference} strokeDashoffset={offset} strokeLinecap="round"
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-display text-3xl font-semibold text-ink">Day {day}</span>
        <span className="text-xs text-ink/60">of {total}-day recovery</span>
      </div>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, tone = "sage" }) {
  const tones = {
    sage: "bg-sage-light text-teal",
    amber: "bg-amber-light text-amber",
    coral: "bg-coral-light text-coral",
  };
  return (
    <div className="bg-white rounded-2xl p-4 shadow-sm border border-black/5">
      <div className={`w-9 h-9 rounded-lg flex items-center justify-center mb-3 ${tones[tone]}`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-xs text-ink/60">{label}</p>
      <p className="font-display text-lg font-semibold">{value}</p>
    </div>
  );
}

export default function Dashboard({ patient, plan, alerts, symptomLog }) {
  const latestSymptom = symptomLog[0];
  const medAdherence = Math.round(
    (plan.medications.reduce((sum, m) => sum + m.taken.filter(Boolean).length, 0) /
      plan.medications.reduce((sum, m) => sum + m.taken.length, 0)) * 100
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold">Welcome back, {patient.name.split(" ")[0]}</h1>
        <p className="text-ink/60 text-sm">{patient.surgery} · Discharged {patient.dischargeDate}</p>
      </div>

      <div className="bg-white rounded-3xl p-6 shadow-sm border border-black/5 flex flex-col sm:flex-row items-center gap-6">
        <HealingRing day={patient.recoveryDay} total={patient.totalRecoveryDays} />
        <div className="flex-1 space-y-2">
          <p className="font-display text-lg font-medium">You're on track</p>
          <p className="text-sm text-ink/70">
            Medication adherence is at {medAdherence}%, and your last wound scan showed normal healing.
            Keep up today's rehab exercises and log your evening check-in.
          </p>
          <div className="flex items-center gap-1 text-sage text-sm font-medium">
            <TrendingUp className="w-4 h-4" /> Recovery trending positively
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Utensils} label="Pain level today" value={`${latestSymptom.pain}/10`} tone={latestSymptom.pain > 6 ? "coral" : "sage"} />
        <StatCard icon={ThermometerSun} label="Fever" value={latestSymptom.fever ? "Reported" : "None"} tone={latestSymptom.fever ? "coral" : "sage"} />
        <StatCard icon={Frown} label="Appetite" value={latestSymptom.appetite} tone={latestSymptom.appetite === "low" ? "amber" : "sage"} />
        <StatCard icon={Bell} label="Medication adherence" value={`${medAdherence}%`} tone={medAdherence < 70 ? "amber" : "sage"} />
      </div>

      <div className="bg-white rounded-2xl p-5 shadow-sm border border-black/5">
        <h2 className="font-display font-semibold mb-3">Recent alerts</h2>
        <div className="space-y-2">
          {alerts.length === 0 && <p className="text-sm text-ink/50">No alerts. Everything looks good.</p>}
          {alerts.map((a) => (
            <div key={a.id} className={`flex items-start gap-3 p-3 rounded-xl ${
              a.severity === "urgent" ? "bg-coral-light" : a.severity === "warning" ? "bg-amber-light" : "bg-sage-light"
            }`}>
              <Bell className="w-4 h-4 mt-0.5 shrink-0" />
              <div>
                <p className="text-sm font-medium">{a.title}</p>
                <p className="text-xs text-ink/60">{a.message} · {a.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}