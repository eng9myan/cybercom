import { ImageResponse } from "next/og";

export const runtime = "edge";
export const alt = "CyberCom Revolution — Intelligent Enterprise Platforms";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          padding: "80px",
          color: "white",
          background: "linear-gradient(135deg, #050505 25%, #18181b 70%, #7c2d12 100%)",
          fontFamily: "Arial, sans-serif",
        }}
      >
        <div style={{ color: "#fb923c", fontSize: 34, marginBottom: 28 }}>CyberCom Revolution</div>
        <div style={{ fontSize: 72, fontWeight: 700, lineHeight: 1.1 }}>
          Intelligent platforms for a connected world.
        </div>
        <div style={{ marginTop: 36, fontSize: 30, color: "#d4d4d8" }}>
          Healthcare · Government · Enterprise
        </div>
      </div>
    ),
    size,
  );
}
