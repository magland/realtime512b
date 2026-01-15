import React from "react";
import { ReceptiveFieldsViewClient } from "./ReceptiveFieldsViewClient";

type ReceptiveFieldsViewProps = {
  width: number;
  height: number;
  client: ReceptiveFieldsViewClient;
};

const ReceptiveFieldsView: React.FunctionComponent<
  ReceptiveFieldsViewProps
> = ({ width, height, client }) => {
  return (
    <div
      style={{
        position: "absolute",
        width,
        height,
        overflow: "auto",
        backgroundColor: "#fff",
      }}
    >
      <div style={{ padding: 20 }}>
        <h2>Receptive Fields (Placeholder)</h2>
        <p>
          This is a placeholder view for receptive fields visualization. The
          actual implementation will be filled in by a colleague.
        </p>
        <div style={{ marginTop: 20 }}>
          <h3>Data dimensions:</h3>
          <ul>
            <li>
              <strong>Units:</strong> {client.numUnits}
            </li>
            <li>
              <strong>Timepoints:</strong> {client.numTimepoints}
            </li>
            <li>
              <strong>Spatial dimensions:</strong> {client.width} x{" "}
              {client.height}
            </li>
            <li>
              <strong>Color channels:</strong> {client.numChannels}
            </li>
          </ul>
          <p style={{ marginTop: 20, color: "#666" }}>
            Total data shape: ({client.numUnits}, {client.numTimepoints},{" "}
            {client.width}, {client.height}, {client.numChannels})
          </p>
        </div>
      </div>
    </div>
  );
};

export default ReceptiveFieldsView;
