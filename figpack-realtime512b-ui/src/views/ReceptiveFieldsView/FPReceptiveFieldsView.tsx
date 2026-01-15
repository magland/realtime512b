/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { FunctionComponent, useEffect, useState } from "react";
import { ZarrGroup } from "../../figpack-interface";
import { ReceptiveFieldsViewClient } from "./ReceptiveFieldsViewClient";
import ReceptiveFieldsView from "./ReceptiveFieldsView";

type FPReceptiveFieldsViewProps = {
  zarrGroup: ZarrGroup;
  width: number;
  height: number;
};

const FPReceptiveFieldsView: FunctionComponent<FPReceptiveFieldsViewProps> = ({
  zarrGroup,
  width,
  height,
}) => {
  const [client, setClient] = useState<ReceptiveFieldsViewClient | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    const load = async () => {
      try {
        const newClient = await ReceptiveFieldsViewClient.create(zarrGroup);
        if (cancelled) return;
        setClient(newClient);
      } catch (err: any) {
        if (cancelled) return;
        console.error("Error loading receptive fields data:", err);
        setErrorMessage(err.message);
      }
    };

    load();

    return () => {
      cancelled = true;
    };
  }, [zarrGroup]);

  if (errorMessage) {
    return (
      <div style={{ padding: 20 }}>
        <h3>Error loading receptive fields</h3>
        <p style={{ color: "red" }}>{errorMessage}</p>
      </div>
    );
  }

  if (!client) {
    return (
      <div style={{ padding: 20 }}>
        <p>Loading receptive fields data...</p>
      </div>
    );
  }

  return <ReceptiveFieldsView width={width} height={height} client={client} />;
};

export default FPReceptiveFieldsView;
