import { ZarrDataset, ZarrGroup } from "../../figpack-interface";

export class ReceptiveFieldsViewClient {
  #zarrGroup: ZarrGroup;
  #numUnits: number;
  #numTimepoints: number;
  #width: number;
  #height: number;
  #numChannels: number;
  #receptiveFieldsDataset: ZarrDataset;

  constructor(
    zarrGroup: ZarrGroup,
    numUnits: number,
    numTimepoints: number,
    width: number,
    height: number,
    numChannels: number,
    receptiveFieldsDataset: ZarrDataset
  ) {
    this.#zarrGroup = zarrGroup;
    this.#numUnits = numUnits;
    this.#numTimepoints = numTimepoints;
    this.#width = width;
    this.#height = height;
    this.#numChannels = numChannels;
    this.#receptiveFieldsDataset = receptiveFieldsDataset;
  }

  static async create(
    zarrGroup: ZarrGroup
  ): Promise<ReceptiveFieldsViewClient> {
    const attrs = zarrGroup.attrs;

    const numUnits = attrs["num_units"] as number;
    const numTimepoints = attrs["num_timepoints"] as number;
    const width = attrs["width"] as number;
    const height = attrs["height"] as number;
    const numChannels = attrs["num_channels"] as number;

    if (
      numUnits === undefined ||
      numTimepoints === undefined ||
      width === undefined ||
      height === undefined ||
      numChannels === undefined
    ) {
      throw new Error("Missing required attributes in zarr group");
    }

    // Get the receptive fields dataset
    const receptiveFieldsDataset = await zarrGroup.getDataset(
      "receptive_fields"
    );
    if (!receptiveFieldsDataset) {
      throw new Error("No receptive_fields dataset found");
    }

    const client = new ReceptiveFieldsViewClient(
      zarrGroup,
      numUnits,
      numTimepoints,
      width,
      height,
      numChannels,
      receptiveFieldsDataset
    );

    return client;
  }

  get numUnits(): number {
    return this.#numUnits;
  }

  get numTimepoints(): number {
    return this.#numTimepoints;
  }

  get width(): number {
    return this.#width;
  }

  get height(): number {
    return this.#height;
  }

  get numChannels(): number {
    return this.#numChannels;
  }

  get receptiveFieldsDataset(): ZarrDataset {
    return this.#receptiveFieldsDataset;
  }
}
