import React, { useState } from "react";
import { LifeBuoy, MapPin, PhoneCall, X } from "lucide-react";

export default function SOSButton({ open, onClose, patient }) {
  const [location, setLocation] = useState(null);
  const [locating, setLocating] = useState(false);
  const [sent, setSent] = useState(false);

  const shareLocation = () => {
    setLocating(true);
    if (!navigator.geolocation) {
      setLocating(false);
      setLocation({ error: "Location services unavailable in this browser" });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocation({ lat: pos.coords.latitude, lng: pos.coords.longitude });
        setLocating(false);
      },
      () => {
        setLocation({ error: "Location permission denied" });
        setLocating(false);
      }
    );
  };

  const sendAlert = () => {
    // In production: POST to /api/alerts with patient id, location, and
    // timestamp — backend fans this out to caregiver + care team via
    // SMS/push notification and, where configured, local emergency services.
    setSent(true);
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-sm w-full p-6 space-y-4 relative">
        <button onClick={onClose} className="absolute top-4 right-4 text-ink/40 hover:text-ink">
          <X className="w-5 h-5" />
        </button>

        <div className="w-12 h-12 rounded-full bg-coral-light text-coral flex items-center justify-center">
          <LifeBuoy className="w-6 h-6" />
        </div>

        <div>
          <h2 className="font-display text-xl font-semibold">Emergency SOS</h2>
          <p className="text-sm text-ink/60 mt-1">
            This will immediately notify {patient.name}'s caregiver and care team, with your current location if shared.
          </p>
        </div>

        {!sent ? (
          <div className="space-y-3">
            <button
              onClick={shareLocation}
              className="w-full flex items-center justify-center gap-2 border border-teal/30 text-teal rounded-xl py-2.5 text-sm font-medium hover:bg-cream transition-colors"
            >
              <MapPin className="w-4 h-4" />
              {locating ? "Getting location…" : location?.lat ? "Location ready" : "Share my location"}
            </button>
            {location?.error && <p className="text-xs text-coral">{location.error}</p>}

            <button
              onClick={sendAlert}
              className="w-full flex items-center justify-center gap-2 bg-coral text-white rounded-xl py-3 text-sm font-semibold hover:bg-coral/90 transition-colors"
            >
              <PhoneCall className="w-4 h-4" /> Alert caregiver & care team now
            </button>
          </div>
        ) : (
          <div className="bg-sage-light text-teal rounded-xl p-4 text-sm">
            Alert sent. Your caregiver and care team have been notified{location?.lat ? " with your location" : ""}.
            If this is a life-threatening emergency, call local emergency services immediately.
          </div>
        )}
      </div>
    </div>
  );
}