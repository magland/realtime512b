import { ZarrGroup } from "../../figpack-interface";

export class MEAFiringRatesAndAmplitudesClient {
  #zarrGroup: ZarrGroup;
  #numFrames: number;
  #numChannels: number;
  #electrodeCoords: Float32Array | null = null;
  #meanFiringRates: Float32Array | null = null;
  #meanSpikeAmplitudes: Float32Array | null = null;
  #maxAmplitude: number = 0;

  constructor(
    zarrGroup: ZarrGroup,
    numFrames: number,
    numChannels: number,
  ) {
    this.#zarrGroup = zarrGroup;
    this.#numFrames = numFrames;
    this.#numChannels = numChannels;
  }

  static async create(
    zarrGroup: ZarrGroup,
  ): Promise<MEAFiringRatesAndAmplitudesClient> {
    const attrs = zarrGroup.attrs;

    const numFrames = attrs["num_frames"] as number;
    const numChannels = attrs["num_channels"] as number;

    if (numFrames === undefined || numChannels === undefined) {
      throw new Error("Missing required attributes in zarr group");
    }

    const client = new MEAFiringRatesAndAmplitudesClient(
      zarrGroup,
      numFrames,
      numChannels,
    );

    // Load all data upfront
    await client.#loadData();

    return client;
  }

  async #loadData(): Promise<void> {
    // Load electrode coordinates
    const coordsDataset = await this.#zarrGroup.getDataset("electrode_coords");
    if (!coordsDataset) {
      throw new Error("No electrode_coords dataset found");
    }
    this.#electrodeCoords = (await coordsDataset.getData({})) as Float32Array;

    // Load mean firing rates (shape: num_frames x num_channels)
    const firingRatesDataset =
      await this.#zarrGroup.getDataset("mean_firing_rates");
    if (!firingRatesDataset) {
      throw new Error("No mean_firing_rates dataset found");
    }
    this.#meanFiringRates = (await firingRatesDataset.getData(
      {},
    )) as Float32Array;

    // Load mean spike amplitudes (shape: num_frames x num_channels)
    const amplitudesDataset = await this.#zarrGroup.getDataset(
      "mean_spike_amplitudes",
    );
    if (!amplitudesDataset) {
      throw new Error("No mean_spike_amplitudes dataset found");
    }
    this.#meanSpikeAmplitudes = (await amplitudesDataset.getData(
      {},
    )) as Float32Array;

    // Calculate global max amplitude across all frames for consistent scaling
    this.#maxAmplitude = Math.max(...Array.from(this.#meanSpikeAmplitudes));
  }

  get numFrames(): number {
    return this.#numFrames;
  }

  get numChannels(): number {
    return this.#numChannels;
  }

  get electrodeCoords(): Float32Array {
    if (!this.#electrodeCoords) {
      throw new Error("Electrode coordinates not loaded");
    }
    return this.#electrodeCoords;
  }

  get maxAmplitude(): number {
    return this.#maxAmplitude;
  }

  // Get firing rates for a specific frame
  getFiringRatesForFrame(frameIndex: number): Float32Array {
    if (!this.#meanFiringRates) {
      throw new Error("Mean firing rates not loaded");
    }
    if (frameIndex < 0 || frameIndex >= this.#numFrames) {
      throw new Error(
        `Frame index ${frameIndex} out of range [0, ${this.#numFrames})`,
      );
    }

    // Extract the slice for this frame
    const start = frameIndex * this.#numChannels;
    const end = start + this.#numChannels;
    return this.#meanFiringRates.slice(start, end);
  }

  // Get amplitudes for a specific frame
  getAmplitudesForFrame(frameIndex: number): Float32Array {
    if (!this.#meanSpikeAmplitudes) {
      throw new Error("Mean spike amplitudes not loaded");
    }
    if (frameIndex < 0 || frameIndex >= this.#numFrames) {
      throw new Error(
        `Frame index ${frameIndex} out of range [0, ${this.#numFrames})`,
      );
    }

    // Extract the slice for this frame
    const start = frameIndex * this.#numChannels;
    const end = start + this.#numChannels;
    return this.#meanSpikeAmplitudes.slice(start, end);
  }
}
