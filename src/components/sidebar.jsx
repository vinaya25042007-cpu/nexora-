import React from "react";
import {
  LayoutDashboard, ClipboardList, ScanLine, Pill, Mic, Stethoscope, LifeBuoy, HeartPulse,
} from "lucide-react";

const NAV_ITEMS = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { key: "plan", label: "Recovery Plan", icon: ClipboardList },
  { key: "wound", label: "Wound Scan", icon: ScanLine },
  { key: "meds", label: "Medications", icon: Pill },
  { key: "voice", label: "Voice Check-in", icon: Mic },
  { key: "doctor", label: "Doctor View", icon: Stethoscope },
];

export default function Sidebar({ active, onNavigate, onSOS }) {
  return (
    <aside className="hidden md:flex md:flex-col w-64 shrink-0 bg-teal text-cream min-h-screen p-6">
      <div className="flex items-center gap-2 mb-10">
        <HeartPulse className="w-7 h-7 text-sage-light" />
        <span className="font-display text-xl font-semibold tracking-tight">Recovery Companion</span>
      </div>

      <nav className="flex-1 flex flex-col gap-1">
        {NAV_ITEMS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => onNavigate(key)}
            className={`flex items-center gap-3 px-4 py-3 rounded-xl text-left transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-sage-light ${
              active === key ? "bg-teal-light text-white" : "text-cream/80 hover:bg-teal-light/60"
            }`}
          >
            <Icon className="w-5 h-5" />
            <span className="text-sm font-medium">{label}</span>
          </button>
        ))}
      </nav>

      <button
        onClick={onSOS}
        className="mt-6 flex items-center justify-center gap-2 bg-coral hover:bg-coral/90 text-white font-semibold py-3 rounded-xl transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-white"
      >
        <LifeBuoy className="w-5 h-5" />
        Emergency SOS
      </button>
    </aside>
  );
}