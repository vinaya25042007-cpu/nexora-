import React, { useState } from "react";
import Sidebar from "./components/Sidebar.jsx";
import Dashboard from "./components/Dashboard.jsx";
import RecoveryPlan from "./components/RecoveryPlan.jsx";
import WoundScan from "./components/WoundScan.jsx";
import Medications from "./components/Medications.jsx";
import VoiceAssistant from "./components/VoiceAssistant.jsx";
import DoctorDashboard from "./components/DoctorDashboard.jsx";
import SOSButton from "./components/SOSButton.jsx";
import {
  initialPatient, initialRecoveryPlan, woundScanHistory, symptomLog, alertsSeed,
} from "./data/mockData.js";
import { LayoutDashboard, ClipboardList, ScanLine, Pill, Mic, Stethoscope, LifeBuoy } from "lucide-react";

const MOBILE_NAV = [
  { key: "dashboard", icon: LayoutDashboard },
  { key: "plan", icon: ClipboardList },
  { key: "wound", icon: ScanLine },
  { key: "meds", icon: Pill },
  { key: "voice", icon: Mic },
  { key: "doctor", icon: Stethoscope },
];

export default function App() {
  const [view, setView] = useState("dashboard");
  const [sosOpen, setSosOpen] = useState(false);

  const [patient] = useState(initialPatient);
  const [plan, setPlan] = useState(initialRecoveryPlan);
  const [woundHistory, setWoundHistory] = useState(woundScanHistory);
  const [alerts, setAlerts] = useState(alertsSeed);

  const handleUrgentWound = (entry) => {
    setAlerts((prev) => [
      {
        id: `a${Date.now()}`,
        severity: "urgent",
        title: "Urgent wound risk detected",
        message: `Scan on ${entry.date} flagged possible infection. Caregiver and care team notified.`,
        time: "just now",
      },
      ...prev,
    ]);
  };

  const handleCheckIn = (transcript) => {
    setAlerts((prev) => [
      { id: `a${Date.now()}`, severity: "info", title: "Voice check-in submitted", message: "Today's symptom check-in was recorded.", time: "just now" },
      ...prev,
    ]);
    setView("dashboard");
  };

  const renderView = () => {
    switch (view) {
      case "dashboard":
        return <Dashboard patient={patient} plan={plan} alerts={alerts} symptomLog={symptomLog} />;
      case "plan":
        return <RecoveryPlan plan={plan} setPlan={setPlan} />;
      case "wound":
        return <WoundScan history={woundHistory} setHistory={setWoundHistory} onUrgent={handleUrgentWound} />;
      case "meds":
        return <Medications plan={plan} setPlan={setPlan} />;
      case "voice":
        return <VoiceAssistant onSubmitCheckIn={handleCheckIn} />;
      case "doctor":
        return <DoctorDashboard patient={patient} plan={plan} woundHistory={woundHistory} alerts={alerts} />;
      default:
        return null;
    }
  };

  return (
    <div className="flex min-h-screen bg-cream">
      <Sidebar active={view} onNavigate={setView} onSOS={() => setSosOpen(true)} />

      <main className="flex-1 p-5 md:p-8 pb-24 md:pb-8 max-w-5xl mx-auto w-full">
        {renderView()}
      </main>

      <nav className="md:hidden fixed bottom-0 inset-x-0 bg-teal flex justify-around items-center py-2 z-40">
        {MOBILE_NAV.map(({ key, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setView(key)}
            className={`p-2 rounded-lg ${view === key ? "text-white" : "text-cream/50"}`}
          >
            <Icon className="w-5 h-5" />
          </button>
        ))}
        <button onClick={() => setSosOpen(true)} className="p-2 rounded-lg text-coral">
          <LifeBuoy className="w-5 h-5" />
        </button>
      </nav>

      <SOSButton open={sosOpen} onClose={() => setSosOpen(false)} patient={patient} />
    </div>
  );
}