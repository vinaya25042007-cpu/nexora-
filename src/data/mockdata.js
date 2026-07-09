// mockData.js — seed state for the demo. In production this comes from the
// discharge-summary parser (AI) and the hospital's EHR/API.

export const initialPatient = {
  name: "Anita Rao",
  age: 58,
  surgery: "Laparoscopic Cholecystectomy (Gallbladder Removal)",
  surgeryDate: "2026-07-02",
  dischargeDate: "2026-07-04",
  surgeon: "Dr. Kavita Menon",
  recoveryDay: 7,
  totalRecoveryDays: 21,
};

export const initialRecoveryPlan = {
  medications: [
    { id: "m1", name: "Paracetamol 650mg", schedule: "Every 8 hours", purpose: "Pain relief", taken: [true, true, false] },
    { id: "m2", name: "Amoxicillin 500mg", schedule: "Twice daily, after food", purpose: "Infection prevention", taken: [true, false] },
    { id: "m3", name: "Pantoprazole 40mg", schedule: "Once daily, before breakfast", purpose: "Acid reflux protection", taken: [true] },
  ],
  rehab: [
    { id: "r1", title: "Deep breathing exercises", frequency: "3x daily, 10 reps", done: true },
    { id: "r2", title: "Short walk (5–10 min)", frequency: "3x daily", done: true },
    { id: "r3", title: "Gentle shoulder stretches", frequency: "2x daily", done: false },
    { id: "r4", title: "Avoid heavy lifting (>5kg)", frequency: "Until day 21", done: false },
  ],
  diet: [
    "Light, low-fat meals for the first 2 weeks",
    "Stay hydrated — 8–10 glasses of water daily",
    "Avoid fried and spicy food",
    "Increase fiber gradually to prevent constipation from painkillers",
  ],
  followUps: [
    { id: "f1", label: "Suture check", date: "2026-07-11", status: "upcoming" },
    { id: "f2", label: "Final follow-up with Dr. Menon", date: "2026-07-23", status: "upcoming" },
  ],
};

export const woundScanHistory = [
  { id: "w1", date: "2026-07-04", risk: "normal", note: "Clean incision, no discharge." },
  { id: "w2", date: "2026-07-06", risk: "normal", note: "Slight redness, expected at this stage." },
];

export const symptomLog = [
  { date: "2026-07-08", pain: 3, fever: false, nausea: false, appetite: "normal" },
  { date: "2026-07-07", pain: 4, fever: false, nausea: true, appetite: "low" },
];

export const alertsSeed = [
  {
    id: "a1",
    severity: "info",
    title: "Follow-up reminder",
    message: "Suture check scheduled in 3 days with Dr. Menon.",
    time: "2h ago",
  },
];