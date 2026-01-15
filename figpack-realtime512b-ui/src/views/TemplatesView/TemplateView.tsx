import React, { useEffect, useRef, useState } from "react";
import { TemplatesViewClient } from "./TemplatesViewClient";
import { valueToColor } from "../MEAMovie/colormapUtils";
import { getUnitColor } from "./unitColors";

type Props = {
  client: TemplatesViewClient;
  width: number;
  height: number;
  unitId: string;
  brightness: number;
  useGlobalScale: boolean;
  globalMin?: number;
  globalMax?: number;
};

const DEFAULT_COLORMAP = "grayscale";
const PADDING = 10; // Padding inside the box for labels and spacing

const TemplateView: React.FC<Props> = ({ 
  client, 
  width, 
  height, 
  unitId, 
  brightness, 
  useGlobalScale, 
  globalMin, 
  globalMax 
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [templateData, setTemplateData] = useState<Float32Array | null>(null);
  const [electrodeRadius, setElectrodeRadius] = useState<number>(5);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Load template data
  useEffect(() => {
    const loadTemplate = async () => {
      try {
        setLoading(true);
        setError(null);

        // Convert unitId to unitIndex (subtract 1)
        const unitIndex = parseInt(unitId, 10) - 1;

        if (unitIndex < 0 || unitIndex >= client.numUnits) {
          throw new Error(`Invalid unit index: ${unitIndex}`);
        }

        // Get template data for this unit
        const data = await client.templatesDataset.getData({
          slice: [[unitIndex, unitIndex + 1]],
        });

        if (!data || data.length !== client.numChannels) {
          throw new Error(
            `Expected ${client.numChannels} channels, got ${data?.length || 0}`,
          );
        }

        setTemplateData(data as Float32Array);

        // Get electrode coordinates and calculate electrode radius
        const electrodeCoords = await client.getElectrodeCoords();
        const coords = new Float32Array(client.numChannels * 2);
        for (let i = 0; i < client.numChannels; i++) {
          coords[i * 2] = electrodeCoords[i][0];
          coords[i * 2 + 1] = electrodeCoords[i][1];
        }
        const minDist = calculateMinElectrodeDistance(coords);
        const radius = (minDist * 0.95) / 2;
        setElectrodeRadius(radius);
      } catch (err) {
        console.error("Error loading template data:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };

    loadTemplate();
  }, [client, unitId]);

  // Render the canvas
  useEffect(() => {
    if (!canvasRef.current || !templateData) return;
    if (useGlobalScale && (globalMin === undefined || globalMax === undefined)) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const canvasWidth = width - 2 * PADDING;
    const canvasHeight = height - 2 * PADDING - 30; // Extra space for label at top

    // Clear canvas
    ctx.fillStyle = "#f4f4f4";
    ctx.fillRect(0, 0, width, height);

    const unitColor = getUnitColor(unitId);

    // Draw unit label at top
    ctx.fillStyle = unitColor;
    ctx.font = "14px Arial";
    ctx.textAlign = "center";
    ctx.fillText(`Unit ${unitId}`, width / 2, 20);

    // Get electrode coordinates (load if needed)
    const loadAndRender = async () => {
      const electrodeCoords = await client.getElectrodeCoords();

      // Calculate bounding box of electrodes
      const numElectrodes = client.numChannels;
      let minX = electrodeCoords[0][0];
      let maxX = electrodeCoords[0][0];
      let minY = electrodeCoords[0][1];
      let maxY = electrodeCoords[0][1];

      for (let i = 0; i < numElectrodes; i++) {
        const x = electrodeCoords[i][0];
        const y = electrodeCoords[i][1];
        if (x < minX) minX = x;
        if (x > maxX) maxX = x;
        if (y < minY) minY = y;
        if (y > maxY) maxY = y;
      }

      // Add internal padding
      const dataWidth = maxX - minX;
      const dataHeight = maxY - minY;

      // Calculate scale to fit canvas with padding
      const scaleX = (canvasWidth) / dataWidth;
      const scaleY = (canvasHeight) / dataHeight;
      const scale = Math.max(0, Math.min(scaleX, scaleY));

      // Calculate offset to center the electrodes
      const offsetX =
        PADDING + (canvasWidth - dataWidth * scale) / 2 - minX * scale;
      const offsetY =
        PADDING + 30 + (canvasHeight - dataHeight * scale) / 2 - minY * scale;

      // Compute min and max from template data or use global
      let dataMin: number;
      let dataMax: number;
      
      if (useGlobalScale && globalMin !== undefined && globalMax !== undefined) {
        dataMin = globalMin;
        dataMax = globalMax;
      } else {
        dataMin = templateData[0];
        dataMax = templateData[0];
        for (let i = 1; i < templateData.length; i++) {
          if (templateData[i] < dataMin) dataMin = templateData[i];
          if (templateData[i] > dataMax) dataMax = templateData[i];
        }
      }
      
      // brightness is between 0 and 100
      // brightness scale should go from -1 (darken) to +1 (brighten)
      let brightnessScale = (brightness - 50) / 50;
      // brightNessScale = brightnessScale ^ (1/4)
      brightnessScale = Math.sign(brightnessScale) * Math.pow(Math.abs(brightnessScale), 1/4);
      dataMin += (dataMax - dataMin) * brightnessScale;

      // Draw electrodes
      for (let i = 0; i < numElectrodes; i++) {
        const x = electrodeCoords[i][0] * scale + offsetX;
        const y = electrodeCoords[i][1] * scale + offsetY;
        const value = templateData[i];

        // Normalize value to [0, 1] range
        const normalizedValue =
          (dataMax - dataMin) > 0 ? (value - dataMin) / (dataMax - dataMin) : 0.5;

        // Invert because spikes are typically negative
        let colorValue = 1 - normalizedValue;
        colorValue = Math.min(1, Math.max(0, colorValue));

        // Apply colormap
        const color = valueToColor(colorValue, DEFAULT_COLORMAP);

        // Draw filled circle
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, electrodeRadius * scale, 0, 2 * Math.PI);
        ctx.fill();
      }
    };

    loadAndRender();
  }, [templateData, electrodeRadius, width, height, client, unitId, brightness, useGlobalScale, globalMin, globalMax]);

  if (loading) {
    return (
      <div
        style={{
          width,
          height,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          backgroundColor: "#f0f0f0",
          border: "1px solid #ccc",
        }}
      >
        Loading...
      </div>
    );
  }

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
          backgroundColor: "#f0f0f0",
          border: "1px solid #ccc",
        }}
      >
        Error: {error}
      </div>
    );
  }

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{
        display: "block",
        border: "1px solid #ccc",
      }}
    />
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

export default TemplateView;
