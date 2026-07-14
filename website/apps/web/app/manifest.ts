import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "CyberCom Revolution",
    short_name: "CyberCom",
    description: "Intelligent platforms for healthcare, government, and enterprise.",
    start_url: "/en",
    display: "standalone",
    background_color: "#050505",
    theme_color: "#f97316",
    icons: [
      {
        src: "/icon.svg",
        sizes: "any",
        type: "image/svg+xml",
        purpose: "any",
      },
    ],
  };
}
