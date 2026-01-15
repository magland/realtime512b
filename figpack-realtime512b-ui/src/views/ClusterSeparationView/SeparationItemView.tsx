import React, { useMemo } from "react";
import { SeparationItem } from "./ClusterSeparationViewClient";

type Props = {
  item: SeparationItem;
  width: number;
  height: number;
  selectedUnitId: string | null;
};

const SeparationItemView: React.FC<Props> = ({
  item,
  width,
  height,
  selectedUnitId,
}) => {
  // Determine display order - selected unit should be on the right (unit 2 position)
  const shouldSwap = selectedUnitId === item.unit_id_1;
  const displayUnitId1 = shouldSwap ? item.unit_id_2 : item.unit_id_1;
  const displayUnitId2 = shouldSwap ? item.unit_id_1 : item.unit_id_2;
  
  // When swapping, negate projections to maintain correct discriminant direction
  const displayProjections1 = shouldSwap 
    ? item.projections_2.map(v => -v)
    : item.projections_1;
  const displayProjections2 = shouldSwap 
    ? item.projections_1.map(v => -v)
    : item.projections_2;

  // Compute histogram data
  const histogramData = useMemo(() => {
    const allValues = [
      ...Array.from(displayProjections1),
      ...Array.from(displayProjections2),
    ];
    
    if (allValues.length === 0) {
      return null;
    }

    const minVal = Math.min(...allValues);
    const maxVal = Math.max(...allValues);
    const range = maxVal - minVal;
    
    if (range === 0) {
      return null;
    }

    const numBins = 50;
    const binWidth = range / numBins;

    // Create bins for both distributions
    const bins1 = new Array(numBins).fill(0);
    const bins2 = new Array(numBins).fill(0);

    for (const val of displayProjections1) {
      const binIndex = Math.min(
        Math.floor((val - minVal) / binWidth),
        numBins - 1
      );
      bins1[binIndex]++;
    }

    for (const val of displayProjections2) {
      const binIndex = Math.min(
        Math.floor((val - minVal) / binWidth),
        numBins - 1
      );
      bins2[binIndex]++;
    }

    // Create sum of bins for background
    const binsSum = bins1.map((count, i) => count + bins2[i]);
    
    const maxCount = Math.max(...binsSum);

    return {
      bins1,
      bins2,
      binsSum,
      minVal,
      maxVal,
      binWidth,
      maxCount,
      numBins,
    };
  }, [displayProjections1, displayProjections2]);

  if (!histogramData) {
    return (
      <div
        style={{
          width,
          height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#f8f8f8",
          fontFamily: "Arial, sans-serif",
          fontSize: "12px",
          color: "#666",
        }}
      >
        No data
      </div>
    );
  }

  const padding = { top: 20, right: 10, bottom: 30, left: 40 };
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  // Use fixed colors instead of unit colors
  const color1 = "#4287f5"; // Blue
  const color2 = "#f54242"; // Red
  
  // Check if zero is in range and calculate its position
  const zeroInRange = histogramData.minVal <= 0 && histogramData.maxVal >= 0;
  const zeroX = zeroInRange 
    ? ((0 - histogramData.minVal) / (histogramData.maxVal - histogramData.minVal)) * plotWidth 
    : null;

  return (
    <div style={{ width, height, position: "relative", backgroundColor: "#fff" }}>
      <svg width={width} height={height}>
        {/* Title */}
        <text
          x={width / 2}
          y={15}
          textAnchor="middle"
          style={{
            fontFamily: "Arial, sans-serif",
            fontSize: "12px",
            fontWeight: "bold",
          }}
        >
          Unit {displayUnitId1} vs Unit {displayUnitId2}
        </text>

        {/* Plot area */}
        <g transform={`translate(${padding.left}, ${padding.top})`}>
          {/* Axes */}
          <line
            x1={0}
            y1={plotHeight}
            x2={plotWidth}
            y2={plotHeight}
            stroke="#333"
            strokeWidth={1}
          />
          <line
            x1={0}
            y1={0}
            x2={0}
            y2={plotHeight}
            stroke="#333"
            strokeWidth={1}
          />

          {/* Zero indicator line (behind everything) */}
          {zeroX !== null && (
            <line
              x1={zeroX}
              y1={0}
              x2={zeroX}
              y2={plotHeight}
              stroke="#999"
              strokeWidth={1.5}
              opacity={0.5}
            />
          )}

          {/* Background histogram bars (sum) in gray */}
          {histogramData.binsSum.map((count, i) => {
            const barHeight = (count / histogramData.maxCount) * plotHeight;
            const x = (i / histogramData.numBins) * plotWidth;
            const barWidth = plotWidth / histogramData.numBins;
            return (
              <rect
                key={`barsum-${i}`}
                x={x}
                y={plotHeight - barHeight}
                width={barWidth}
                height={barHeight}
                fill="#999"
                opacity={0.3}
                stroke="#999"
                strokeWidth={0.5}
              />
            );
          })}

          {/* Histogram bars for unit 1 */}
          {histogramData.bins1.map((count, i) => {
            const barHeight = (count / histogramData.maxCount) * plotHeight;
            const x = (i / histogramData.numBins) * plotWidth;
            const barWidth = plotWidth / histogramData.numBins;
            return (
              <rect
                key={`bar1-${i}`}
                x={x}
                y={plotHeight - barHeight}
                width={barWidth}
                height={barHeight}
                fill={color1}
                opacity={0.5}
                stroke={color1}
                strokeWidth={0.5}
              />
            );
          })}

          {/* Histogram bars for unit 2 */}
          {histogramData.bins2.map((count, i) => {
            const barHeight = (count / histogramData.maxCount) * plotHeight;
            const x = (i / histogramData.numBins) * plotWidth;
            const barWidth = plotWidth / histogramData.numBins;
            return (
              <rect
                key={`bar2-${i}`}
                x={x}
                y={plotHeight - barHeight}
                width={barWidth}
                height={barHeight}
                fill={color2}
                opacity={0.5}
                stroke={color2}
                strokeWidth={0.5}
              />
            );
          })}

          {/* X-axis label */}
          <text
            x={plotWidth / 2}
            y={plotHeight + 25}
            textAnchor="middle"
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: "10px",
            }}
          >
            Projection
          </text>

          {/* Y-axis label */}
          <text
            x={-plotHeight / 2}
            y={-25}
            textAnchor="middle"
            transform={`rotate(-90, ${-plotHeight / 2}, -25)`}
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: "10px",
            }}
          >
            Count
          </text>
        </g>

        {/* Legend */}
        <g transform={`translate(${width - 80}, ${padding.top})`}>
          <rect x={0} y={0} width={12} height={12} fill={color1} opacity={0.5} />
          <text
            x={16}
            y={10}
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: "10px",
            }}
          >
            Unit {displayUnitId1}
          </text>
          <rect x={0} y={16} width={12} height={12} fill={color2} opacity={0.5} />
          <text
            x={16}
            y={26}
            style={{
              fontFamily: "Arial, sans-serif",
              fontSize: "10px",
            }}
          >
            Unit {displayUnitId2}
          </text>
        </g>
      </svg>
    </div>
  );
};

export default SeparationItemView;
