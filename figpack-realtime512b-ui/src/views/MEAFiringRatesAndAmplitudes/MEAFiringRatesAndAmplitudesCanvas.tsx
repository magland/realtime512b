import React, { useEffect, useRef, useState } from "react";
import { MEAFiringRatesAndAmplitudesClient } from "./MEAFiringRatesAndAmplitudesClient";
import { valueToColor } from "../MEAMovie/colormapUtils";

// Maximum firing rate for radius scaling (Hz)
const MAX_FIRING_RATE_HZ = 300.0;

type Props = {
  client: MEAFiringRatesAndAmplitudesClient;
  frameIndex: number;
  width: number;
  height: number;
};

type HoverInfo = {
  channelIndex: number;
  firingRate: number;
  amplitude: number;
  x: number;
  y: number;
} | null;

const MEAFiringRatesAndAmplitudesCanvas: React.FC<Props> = ({
  client,
  frameIndex,
  width,
  height,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoverInfo, setHoverInfo] = useState<HoverInfo>(null);
  const [error, setError] = useState<string | null>(null);

  // Store electrode screen positions for hover detection
  const electrodeScreenPositionsRef = useRef<
    { x: number; y: number; radius: number; channelIndex: number }[]
  >([]);

  // Render the canvas
  useEffect(() => {
    if (!canvasRef.current) return;

    try {
      const canvas = canvasRef.current;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;

      const electrodeCoords = client.electrodeCoords;
      const firingRates = client.getFiringRatesForFrame(frameIndex);
      const amplitudes = client.getAmplitudesForFrame(frameIndex);
      const maxAmplitude = client.maxAmplitude;
      const numElectrodes = client.numChannels;

      // Clear canvas
      ctx.fillStyle = "#f5f5f5";
      ctx.fillRect(0, 0, width, height);

      // Calculate bounding box of electrodes
      let minX = electrodeCoords[0];
      let maxX = electrodeCoords[0];
      let minY = electrodeCoords[1];
      let maxY = electrodeCoords[1];

      for (let i = 0; i < numElectrodes; i++) {
        const x = electrodeCoords[i * 2];
        const y = electrodeCoords[i * 2 + 1];
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }

      // Calculate minimum electrode distance for sizing
      const minElectrodeDist = calculateMinElectrodeDistance(electrodeCoords);

      // Add padding
      const padding = 60;
      const dataWidth = maxX - minX;
      const dataHeight = maxY - minY;

      // Calculate scale to fit canvas with padding
      const scaleX = (width - 2 * padding) / dataWidth;
      const scaleY = (height - 2 * padding) / dataHeight;
      const scale = Math.max(0, Math.min(scaleX, scaleY));

      // Calculate offset to center the electrodes
      const offsetX = (width - dataWidth * scale) / 2 - minX * scale;
      const offsetY = (height - dataHeight * scale) / 2 - minY * scale;

      // Calculate base radius from minimum electrode distance
      const baseRadius = (minElectrodeDist * scale * 0.9) / 2;

      // Clear screen positions array
      electrodeScreenPositionsRef.current = [];

      // Draw electrodes
      for (let i = 0; i < numElectrodes; i++) {
        const x = electrodeCoords[i * 2] * scale + offsetX;
        const y = electrodeCoords[i * 2 + 1] * scale + offsetY;
        const firingRate = firingRates[i];
        const amplitude = amplitudes[i];

        // Calculate radius based on firing rate (0-MAX_FIRING_RATE_HZ maps to 0-baseRadius)
        const normalizedFiringRate = Math.min(firingRate / MAX_FIRING_RATE_HZ, 1.0);
        const radius = normalizedFiringRate * baseRadius;

        // Calculate color based on amplitude (Viridis colormap)
        const normalizedAmplitude =
          maxAmplitude > 0 ? amplitude / maxAmplitude : 0;
        const color = valueToColor(normalizedAmplitude, "viridis");

        // Store screen position for hover detection
        electrodeScreenPositionsRef.current.push({
          x,
          y,
          radius,
          channelIndex: i,
        });

        // Draw filled circle
        if (radius > 0) {
          ctx.fillStyle = color;
          ctx.beginPath();
          ctx.arc(x, y, radius, 0, 2 * Math.PI);
          ctx.fill();

          // Add subtle border
          ctx.strokeStyle = "rgba(0, 0, 0, 0.3)";
          ctx.lineWidth = 1;
          ctx.stroke();
        } else {
          // For zero firing rate, draw a small gray dot
          ctx.fillStyle = "#cccccc";
          ctx.beginPath();
          ctx.arc(x, y, 2, 0, 2 * Math.PI);
          ctx.fill();
        }
      }

      // Highlight hovered electrode
      if (hoverInfo) {
        const hoveredElectrode = electrodeScreenPositionsRef.current.find(
          (e) => e.channelIndex === hoverInfo.channelIndex,
        );
        if (hoveredElectrode) {
          ctx.strokeStyle = "rgba(255, 0, 0, 0.8)";
          ctx.lineWidth = 3;
          ctx.beginPath();
          ctx.arc(
            hoveredElectrode.x,
            hoveredElectrode.y,
            Math.max(hoveredElectrode.radius, 4),
            0,
            2 * Math.PI,
          );
          ctx.stroke();
        }
      }
    } catch (err) {
      console.error("Error rendering canvas:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }, [client, frameIndex, width, height, hoverInfo]);

  // Handle mouse move for hover detection
  const handleMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = event.clientX - rect.left;
    const mouseY = event.clientY - rect.top;

    // Find electrode under cursor
    let foundHover: HoverInfo = null;
    for (const electrode of electrodeScreenPositionsRef.current) {
      const dx = mouseX - electrode.x;
      const dy = mouseY - electrode.y;
      const distance = Math.sqrt(dx * dx + dy * dy);

      // Check if mouse is within electrode radius (or at least 4px for small electrodes)
      if (distance <= Math.max(electrode.radius, 4)) {
        const firingRates = client.getFiringRatesForFrame(frameIndex);
        const amplitudes = client.getAmplitudesForFrame(frameIndex);

        foundHover = {
          channelIndex: electrode.channelIndex,
          firingRate: firingRates[electrode.channelIndex],
          amplitude: amplitudes[electrode.channelIndex],
          x: mouseX,
          y: mouseY,
        };
        break;
      }
    }

    setHoverInfo(foundHover);
  };

  const handleMouseLeave = () => {
    setHoverInfo(null);
  };

  if (error) {
    return (
      <div
        style={{
          width,
          height,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          color: "red",
        }}
      >
        Error: {error}
      </div>
    );
  }

  return (
    <div style={{ position: "relative", width, height }}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{
          display: "block",
          cursor: hoverInfo ? "pointer" : "default",
        }}
      />
      {hoverInfo && (
        <div
          style={{
            position: "absolute",
            left: hoverInfo.x + 15,
            top: hoverInfo.y - 10,
            backgroundColor: "rgba(0, 0, 0, 0.85)",
            color: "white",
            padding: "8px 12px",
            borderRadius: "4px",
            fontSize: "13px",
            pointerEvents: "none",
            whiteSpace: "nowrap",
            boxShadow: "0 2px 8px rgba(0,0,0,0.3)",
            zIndex: 1000,
          }}
        >
          <div>
            <strong>Channel {hoverInfo.channelIndex}</strong>
          </div>
          <div>Firing Rate: {hoverInfo.firingRate.toFixed(2)} Hz</div>
          <div>Amplitude: {hoverInfo.amplitude.toFixed(2)} μV</div>
        </div>
      )}
    </div>
  );
};

// Helper function to calculate minimum distance between electrodes
function calculateMinElectrodeDistance(coords: Float32Array): number {
  const numElectrodes = coords.length / 2;
  let minDist = Infinity;

  for (let i = 0; i < numElectrodes; i++) {
    const x1 = coords[i * 2];
    const y1 = coords[i * 2 + 1];

    for (let j = i + 1; j < numElectrodes; j++) {
      const x2 = coords[j * 2];
      const y2 = coords[j * 2 + 1];

      const dist = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
      if (dist > 0 && dist < minDist) {
        minDist = dist;
      }
    }
  }

  return minDist === Infinity ? 10 : minDist;
}

export default MEAFiringRatesAndAmplitudesCanvas;
