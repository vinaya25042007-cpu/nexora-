import React, { useState, useRef } from "react";
import { Mic, MicOff, Sparkles } from "lucide-react";

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

const PROMPTS = [
  "How would you rate your pain today, from 0 to 10?",
  "Have you noticed any fever or chills?",
  "How is your appetite today?",
  "Any redness, swelling, or discharge near your incision?",
];

export default function VoiceAssistant({ onSubmitCheckIn }) {
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [promptIdx, setPromptIdx] = useState(0);
  const [supported] = useState(!!SpeechRecognition);
  const recognitionRef = useRef(null);

  const startListening = () => {
    if (!supported) return;
    const recognition = new SpeechRecognition();
    recognition.lang = "en-IN";
    recognition.interimResults = false;
    recognition.onresult = (e) => {
      const text = e.results[0][0].transcript;
      setTranscript((prev) => `${prev}\n${PROMPTS[promptIdx]}\n→ ${text}`);
      setPromptIdx((i) => Math.min(i + 1, PROMPTS.length - 1));
    };
    recognition.onend = () => setListening(false);
    recognition.start();
    recognitionRef.current = recognition;
    setListening(true);
  };

  const stopListening = () => {
    recognitionRef.current?.stop();
    setListening(false);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-semibold">Voice Check-in</h1>
        <p className="text-ink/60 text-sm">Hands-free daily symptom check-in — helpful when movement is limited post-surgery.</p>
      </div>

      <div className="bg-white rounded-2xl p-8 shadow-sm border border-black/5 flex flex-col items-center text-center gap-4">
        {!supported && (
          <p className="text-sm text-amber bg-amber-light rounded-xl p-3">
            Voice recognition isn't supported in this browser. Try Chrome on desktop or Android.
          </p>
        )}

        <p className="font-display text-lg font-medium">{PROMPTS[promptIdx]}</p>

        <button
          onClick={listening ? stopListening : startListening}
          disabled={!supported}
          className={`w-20 h-20 rounded-full flex items-center justify-center transition-colors ${
            listening ? "bg-coral text-white animate-pulse" : "bg-teal text-white hover:bg-teal-light"
          } disabled:opacity-40`}
        >
          {listening ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
        </button>
        <p className="text-xs text-ink/50">{listening ? "Listening… speak now" : "Tap to answer by voice"}</p>

        {transcript && (
          <div className="w-full text-left bg-cream rounded-xl p-4 text-sm whitespace-pre-line mt-2">
            {transcript}
          </div>
        )}

        {promptIdx === PROMPTS.length - 1 && transcript && (
          <button
            onClick={() => onSubmitCheckIn(transcript)}
            className="flex items-center gap-2 bg-sage text-white px-5 py-2.5 rounded-xl font-medium hover:bg-sage/90 transition-colors"
          >
            <Sparkles className="w-4 h-4" /> Submit check-in
          </button>
        )}
      </div>
    </div>
  );
}