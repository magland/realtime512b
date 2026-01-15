import React from "react";
import {
  FPViewContext,
  FPViewContexts,
  ZarrGroup
} from "../../figpack-interface";
import ClusterSeparationView from "./ClusterSeparationView";
import UnitSelectionContext, { UnitSelection, UnitSelectionAction } from "../TemplatesView/context-unit-selection/UnitSelectionContext";
import { useProvideFPViewContext } from "../../figpack-utils";

type Props = {
  zarrGroup: ZarrGroup;
  contexts: FPViewContexts;
  width: number;
  height: number;
};

const FPClusterSeparationView: React.FC<Props> = ({ zarrGroup, width, height, contexts }) => {
  return (
    <ProvideUnitSelectionContext context={contexts.unitSelection}>
      <ClusterSeparationView zarrGroup={zarrGroup} width={width} height={height} />
    </ProvideUnitSelectionContext>
  );
};

const ProvideUnitSelectionContext: React.FC<{
  context: FPViewContext;
  children: React.ReactNode;
}> = ({ context, children }) => {
  const { state, dispatch } = useProvideFPViewContext<
    UnitSelection,
    UnitSelectionAction
  >(context);

  if (!dispatch || !state) {
    return <>Waiting for context...</>;
  }

  return (
    <UnitSelectionContext.Provider
      value={{ unitSelection: state, unitSelectionDispatch: dispatch }}
    >
      {children}
    </UnitSelectionContext.Provider>
  );
};

export default FPClusterSeparationView;
