import React, { useEffect, useState } from "react";
import { ZarrGroup } from "../../figpack-interface";
import { MEAFiringRatesAndAmplitudesClient } from "./MEAFiringRatesAndAmplitudesClient";
import MEAFiringRatesAndAmplitudesCanvas from "./MEAFiringRatesAndAmplitudesCanvas";
import { valueToColor } from "../MEAMovie/colormapUtils";

// Maximum firing rate for radius scaling (Hz)
const MAX_FIRING_RATE_HZ = 300.0;

type Props = {
  zarrGroup: ZarrGroup;
  width: number;
  height: number;
};

const MEAFiringRatesAndAmplitudesView: React.FC<Props> = ({
  zarrGroup,
  width,
  height,
}) => {
  const [client, setClient] =
    useState<MEAFiringRatesAndAmplitudesClient | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [currentFrameIndex, setCurrentFrameIndex] = useState<number>(0);

  const legendWidth = 250;
  const controlsHeight = 80;
  const legendHeight = height;
  const canvasWidth = width - legendWidth;
  // Only show controls if there's more than one frame
  const showControls = client && client.numFrames > 1;
  const canvasHeight = height - (showControls ? controlsHeight : 0);

  // Load the client
  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);

        const meaClient = await MEAFiringRatesAndAmplitudesClient.create(
          zarrGroup,
        );
        setClient(meaClient);
      } catch (err) {
        console.error(
          "Error loading MEA Firing Rates and Amplitudes client:",
          err,
        );
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [zarrGroup]);

  if (loading) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          width,
          height,
          fontFamily: "Arial, sans-serif",
          backgroundColor: "#f5f5f5",
        }}
      >
        Loading Firing Rates and Amplitudes data...
      </div>
    );
  }

  if (error || !client) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          width,
          height,
          fontFamily: "Arial, sans-serif",
          color: "red",
          backgroundColor: "#f5f5f5",
        }}
      >
        Error: {error || "Failed to load data"}
      </div>
    );
  }

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "row",
        width,
        height,
        fontFamily: "Arial, sans-serif",
        backgroundColor: "#f5f5f5",
      }}
    >
      {/* Main visualization area */}
      <div
        style={{
          width: canvasWidth,
          height,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Canvas */}
        <div style={{ width: canvasWidth, height: canvasHeight }}>
          <MEAFiringRatesAndAmplitudesCanvas
            client={client}
            frameIndex={currentFrameIndex}
            width={canvasWidth}
            height={canvasHeight}
          />
        </div>

        {/* Navigation Controls - Only show if there's more than one frame */}
        {showControls && (
          <div
            style={{
              height: controlsHeight,
              padding: "15px 20px",
              backgroundColor: "#2a2a2a",
              borderTop: "1px solid #444",
              display: "flex",
              flexDirection: "column",
              gap: "12px",
            }}
          >
            {/* Buttons and frame info */}
            <div
              style={{
                display: "flex",
                alignItems: "center",
                gap: "12px",
              }}
            >
              <button
                onClick={() =>
                  setCurrentFrameIndex(Math.max(0, currentFrameIndex - 1))
                }
                disabled={currentFrameIndex === 0}
                style={{
                  padding: "6px 14px",
                  fontSize: "13px",
                  backgroundColor:
                    currentFrameIndex === 0 ? "#555" : "#4a90e2",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor: currentFrameIndex === 0 ? "not-allowed" : "pointer",
                  fontWeight: "bold",
                }}
              >
                ← Prev
              </button>

              <button
                onClick={() =>
                  setCurrentFrameIndex(
                    Math.min(client.numFrames - 1, currentFrameIndex + 1),
                  )
                }
                disabled={currentFrameIndex === client.numFrames - 1}
                style={{
                  padding: "6px 14px",
                  fontSize: "13px",
                  backgroundColor:
                    currentFrameIndex === client.numFrames - 1
                      ? "#555"
                      : "#4a90e2",
                  color: "white",
                  border: "none",
                  borderRadius: "4px",
                  cursor:
                    currentFrameIndex === client.numFrames - 1
                      ? "not-allowed"
                      : "pointer",
                  fontWeight: "bold",
                }}
              >
                Next →
              </button>

              <div
                style={{
                  marginLeft: "auto",
                  fontSize: "13px",
                  color: "#ccc",
                  fontWeight: "500",
                }}
              >
                Frame: {currentFrameIndex + 1} / {client.numFrames}
              </div>
            </div>

            {/* Slider */}
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <span
                style={{
                  fontSize: "12px",
                  color: "#ccc",
                  minWidth: "45px",
                }}
              >
                Frame:
              </span>
              <input
                type="range"
                min={0}
                max={client.numFrames - 1}
                value={currentFrameIndex}
                onChange={(e) =>
                  setCurrentFrameIndex(parseInt(e.target.value, 10))
                }
                style={{
                  flex: 1,
                  height: "6px",
                  background: "#4a4a4a",
                  outline: "none",
                  borderRadius: "3px",
                  cursor: "pointer",
                }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div
        style={{
          width: legendWidth,
          height: legendHeight,
          padding: "20px",
          backgroundColor: "#ffffff",
          borderLeft: "1px solid #ddd",
          overflowY: "auto",
        }}
      >
        <h3
          style={{
            margin: "0 0 20px 0",
            fontSize: "16px",
            fontWeight: "bold",
            color: "#333",
          }}
        >
          Legend
        </h3>

        {/* Firing Rate Section */}
        <div style={{ marginBottom: "30px" }}>
          <h4
            style={{
              margin: "0 0 12px 0",
              fontSize: "14px",
              fontWeight: "600",
              color: "#555",
            }}
          >
            Circle Size: Firing Rate
          </h4>
          <div style={{ fontSize: "12px", color: "#666", lineHeight: "1.6" }}>
            <div style={{ marginBottom: "8px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  marginBottom: "6px",
                }}
              >
                <div
                  style={{
                    width: "30px",
                    height: "30px",
                    borderRadius: "50%",
                    backgroundColor: "#888",
                    marginRight: "10px",
                  }}
                />
                <span>{MAX_FIRING_RATE_HZ} Hz (max)</span>
              </div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  marginBottom: "6px",
                }}
              >
                <div
                  style={{
                    width: "15px",
                    height: "15px",
                    borderRadius: "50%",
                    backgroundColor: "#888",
                    marginRight: "10px",
                    marginLeft: "7.5px",
                  }}
                />
                <span>{MAX_FIRING_RATE_HZ / 2} Hz</span>
              </div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                }}
              >
                <div
                  style={{
                    width: "4px",
                    height: "4px",
                    borderRadius: "50%",
                    backgroundColor: "#ccc",
                    marginRight: "10px",
                    marginLeft: "13px",
                  }}
                />
                <span>0 Hz</span>
              </div>
            </div>
          </div>
        </div>

        {/* Amplitude Color Section */}
        <div style={{ marginBottom: "20px" }}>
          <h4
            style={{
              margin: "0 0 12px 0",
              fontSize: "14px",
              fontWeight: "600",
              color: "#555",
            }}
          >
            Color: Spike Amplitude
          </h4>
          <div style={{ fontSize: "12px", color: "#666", lineHeight: "1.6" }}>
            <div
              style={{
                marginBottom: "8px",
                fontStyle: "italic",
              }}
            >
              0 to {client.maxAmplitude.toFixed(1)} μV
            </div>
            <ColorGradientBar maxAmplitude={client.maxAmplitude} />
          </div>
        </div>

        {/* Info Section */}
        <div
          style={{
            marginTop: "30px",
            padding: "12px",
            backgroundColor: "#f8f9fa",
            borderRadius: "4px",
            fontSize: "12px",
            color: "#666",
          }}
        >
          <div style={{ marginBottom: "8px" }}>
            <strong>Total Channels:</strong> {client.numChannels}
          </div>
          <div style={{ marginBottom: "8px" }}>
            <strong>Hover</strong> over electrodes to see exact values
          </div>
        </div>
      </div>
    </div>
  );
};

// Component to render color gradient bar
const ColorGradientBar: React.FC<{ maxAmplitude: number }> = ({
  maxAmplitude,
}) => {
  const gradientHeight = 120;
  const gradientWidth = 30;

  // Create gradient steps
  const steps = 50;
  const gradientSteps = [];
  for (let i = 0; i < steps; i++) {
    const value = i / (steps - 1);
    const color = valueToColor(value, "viridis");
    gradientSteps.push(color);
  }

  const gradientString = gradientSteps
    .map((color, i) => {
      const percent = (i / (steps - 1)) * 100;
      return `${color} ${percent}%`;
    })
    .join(", ");

  return (
    <div style={{ display: "flex", alignItems: "center", marginTop: "10px" }}>
      <div
        style={{
          width: `${gradientWidth}px`,
          height: `${gradientHeight}px`,
          background: `linear-gradient(to top, ${gradientString})`,
          border: "1px solid #ccc",
          borderRadius: "2px",
        }}
      />
      <div
        style={{
          marginLeft: "10px",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          height: `${gradientHeight}px`,
          fontSize: "11px",
        }}
      >
        <div>{maxAmplitude.toFixed(1)}</div>
        <div>{(maxAmplitude / 2).toFixed(1)}</div>
        <div>0</div>
      </div>
    </div>
  );
};

export default MEAFiringRatesAndAmplitudesView;
