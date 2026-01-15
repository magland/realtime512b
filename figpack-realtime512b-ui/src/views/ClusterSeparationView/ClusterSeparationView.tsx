import React, { useEffect, useMemo, useState } from "react";
import { ZarrGroup } from "../../figpack-interface";
import { ClusterSeparationViewClient, SeparationItem } from "./ClusterSeparationViewClient";
import SeparationItemView from "./SeparationItemView";
import { useSelectedUnitIds } from "../TemplatesView/context-unit-selection/UnitSelectionContext";

type Props = {
  width: number;
  height: number;
  zarrGroup: ZarrGroup;
};

const ClusterSeparationView: React.FC<Props> = ({ width, height, zarrGroup }) => {
  const [client, setClient] = useState<ClusterSeparationViewClient | null>(null);
  const [items, setItems] = useState<SeparationItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const { selectedUnitIdsArray: selectedUnitIds } = useSelectedUnitIds();

  // Load the client and items
  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const separationClient = await ClusterSeparationViewClient.create(zarrGroup);
        const loadedItems = await separationClient.getItems();
        setClient(separationClient);
        setItems(loadedItems);
      } catch (err) {
        console.error("Error loading Cluster Separation View client:", err);
        setError(err instanceof Error ? err.message : "Unknown error");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [zarrGroup]);

  // Filter items to show only those involving the selected unit
  const displayItems = useMemo(() => {
    if (selectedUnitIds.length === 0) {
      return [];
    }

    const selectedId = selectedUnitIds[0]; // Use first selected unit
    return items.filter(
      (item) => item.unit_id_1 === selectedId || item.unit_id_2 === selectedId
    );
  }, [items, selectedUnitIds]);

  const boxMargin = 20;
  const boxWidth = useMemo(() => {
    if (width < 400) {
      return width - boxMargin * 2;
    } else if (width < 800) {
      return (width - boxMargin * 3) / 2;
    } else if (width < 1200) {
      return (width - boxMargin * 4) / 3;
    } else {
      return (width - boxMargin * 5) / 4;
    }
  }, [width]);

  const aspectRatio = 1.3;
  const boxHeight = boxWidth / aspectRatio;

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
        }}
      >
        Loading Cluster Separation View data...
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
        }}
      >
        Error: {error || "Failed to load Cluster Separation View data"}
      </div>
    );
  }

  if (selectedUnitIds.length === 0) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          width,
          height,
          fontFamily: "Arial, sans-serif",
          color: "#666",
          backgroundColor: "#f8f8f8",
        }}
      >
        Select a unit to view cluster separation
      </div>
    );
  }

  if (displayItems.length === 0) {
    return (
      <div
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          width,
          height,
          fontFamily: "Arial, sans-serif",
          color: "#666",
          backgroundColor: "#f8f8f8",
        }}
      >
        No separation data available for selected unit {selectedUnitIds[0]}
      </div>
    );
  }

  return (
    <div
      style={{
        width,
        height,
        overflowY: "auto",
        overflowX: "hidden",
        backgroundColor: "#f8f8f8",
        padding: boxMargin,
      }}
    >
      <div
        style={{
          marginBottom: boxMargin,
          fontFamily: "Arial, sans-serif",
          fontSize: "14px",
          color: "#333",
        }}
      >
        Showing separation for Unit {selectedUnitIds[0]} ({displayItems.length} pairs)
      </div>
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: `${boxMargin}px`,
          alignContent: "flex-start",
        }}
      >
        {displayItems.map((item) => (
          <div
            key={`${item.unit_id_1}-${item.unit_id_2}`}
            style={{
              width: boxWidth,
              height: boxHeight,
              flexShrink: 0,
              border: "1px solid #ddd",
              borderRadius: "4px",
              boxSizing: "border-box",
              backgroundColor: "#fff",
            }}
          >
            <SeparationItemView
              item={item}
              width={boxWidth}
              height={boxHeight}
              selectedUnitId={String(selectedUnitIds[0])}
            />
          </div>
        ))}
      </div>
    </div>
  );
};

export default ClusterSeparationView;
