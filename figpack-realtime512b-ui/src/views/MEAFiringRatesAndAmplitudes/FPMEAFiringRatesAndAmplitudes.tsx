import React from "react";
import { FPViewContexts, ZarrGroup } from "../../figpack-interface";
import MEAFiringRatesAndAmplitudesView from "./MEAFiringRatesAndAmplitudesView";

type Props = {
  zarrGroup: ZarrGroup;
  contexts: FPViewContexts;
  width: number;
  height: number;
};

const FPMEAFiringRatesAndAmplitudes: React.FC<Props> = ({
  zarrGroup,
  width,
  height,
}) => {
  return (
    <MEAFiringRatesAndAmplitudesView
      zarrGroup={zarrGroup}
      width={width}
      height={height}
    />
  );
};

export default FPMEAFiringRatesAndAmplitudes;
