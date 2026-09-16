export const metadata = { title: "Offline — CyEd" };

export default function OfflinePage() {
  return (
    <div className="card" style={{ padding: "2rem", maxWidth: 480 }}>
      <h1 className="text-xl font-bold mb-2">You&rsquo;re offline</h1>
      <p style={{ color: "var(--muted)" }}>
        CyEd can&rsquo;t reach the network right now. Pages you&rsquo;ve already opened stay
        available; live data (attendance, grades, fees) will refresh once you&rsquo;re back
        online.
      </p>
    </div>
  );
}
