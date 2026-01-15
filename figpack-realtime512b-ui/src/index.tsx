/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { FunctionComponent, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import FPMEAMovie from "./views/MEAMovie/FPMEAMovie";
import FPMEASpikeFramesMovie from "./views/MEASpikeFramesMovie/FPMEASpikeFramesMovie";
import {
  FPViewComponent,
  FPViewContext,
  RenderParams,
  ZarrGroup,
} from "./figpack-interface";
import FPMEAFiringRatesAndAmplitudes from "./views/MEAFiringRatesAndAmplitudes/FPMEAFiringRatesAndAmplitudes";
import FPTemplatesView from "./views/TemplatesView/FPTemplatesView";
import FPClusterSeparationView from "./views/ClusterSeparationView/FPClusterSeparationView";
import FPReceptiveFieldsView from "./views/ReceptiveFieldsView/FPReceptiveFieldsView";

// Declare global types for figpack extension system
export {};

type ComponentWrapperProps = {
  zarrGroup: ZarrGroup;
  width: number;
  height: number;
  onResize: (callback: (width: number, height: number) => void) => void;
  onDataChange: (callback: (zarrGroup: ZarrGroup) => void) => void;
  contexts: { [key: string]: FPViewContext };
  component: React.ComponentType<any>;
  renderFPView: (params: RenderParams) => void;
};

// eslint-disable-next-line react-refresh/only-export-components
const ComponentWrapper: FunctionComponent<ComponentWrapperProps> = ({
  zarrGroup,
  width,
  height,
  onResize,
  onDataChange,
  contexts,
  component: Component,
  renderFPView,
}) => {
  const [internalWidth, setInternalWidth] = useState(width);
  const [internalHeight, setInternalHeight] = useState(height);
  const [internalZarrGroup, setInternalZarrGroup] = useState(zarrGroup);

  useEffect(() => {
    onResize((newWidth, newHeight) => {
      setInternalWidth(newWidth);
      setInternalHeight(newHeight);
    });
    onDataChange((newZarrGroup) => {
      setInternalZarrGroup(newZarrGroup);
    });
  }, [onResize, onDataChange]);

  return (
    <Component
      zarrGroup={internalZarrGroup}
      width={internalWidth}
      height={internalHeight}
      contexts={contexts}
      renderFPView={renderFPView}
    />
  );
};

const makeRenderFunction = (Component: React.ComponentType<any>) => {
  return (a: RenderParams) => {
    const {
      container,
      zarrGroup,
      width,
      height,
      onResize,
      onDataChange,
      contexts,
      renderFPView
    } = a;
    const root = createRoot(container);
    root.render(
      <ComponentWrapper
        zarrGroup={zarrGroup}
        width={width}
        height={height}
        onResize={onResize}
        onDataChange={onDataChange}
        contexts={contexts}
        component={Component}
        renderFPView={renderFPView}
      />,
    );
  };
};

const registerExtension = () => {
  // Register view components
  const registerFPViewComponent: (v: FPViewComponent) => void = (window as any)
    .figpack_p1.registerFPViewComponent;
  
  registerFPViewComponent({
    name: "realtime512b.MEAMovie",
    render: makeRenderFunction(FPMEAMovie),
  });

  registerFPViewComponent({
    name: "realtime512b.MEASpikeFramesMovie",
    render: makeRenderFunction(FPMEASpikeFramesMovie),
  });

  registerFPViewComponent({
    name: "realtime512b.TemplatesView",
    render: makeRenderFunction(
      FPTemplatesView
    ),
  });

  registerFPViewComponent({
    name: "realtime512b.MEAFiringRatesAndAmplitudes",
    render: makeRenderFunction(FPMEAFiringRatesAndAmplitudes),
  });

  registerFPViewComponent({
    name: "realtime512b.ClusterSeparationView",
    render: makeRenderFunction(FPClusterSeparationView),
  });

  registerFPViewComponent({
    name: "realtime512b.ReceptiveFieldsView",
    render: makeRenderFunction(FPReceptiveFieldsView),
  });

  // Register extension
  const registerFPExtension: (e: { name: string }) => void = (window as any)
    .figpack_p1.registerFPExtension;
  registerFPExtension({ name: "figpack-realtime512b" });
};

registerExtension();
