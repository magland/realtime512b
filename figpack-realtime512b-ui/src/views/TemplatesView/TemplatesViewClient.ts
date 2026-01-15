import { ZarrDataset, ZarrGroup } from "../../figpack-interface";

export class TemplatesViewClient {
  #zarrGroup: ZarrGroup;
  #numTemplates: number;
  #numChannels: number;
  #templatesDataset: ZarrDataset;
  #electrodeCoords: number[][] | null = null;

  constructor(
    zarrGroup: ZarrGroup,
    numTemplates: number,
    numChannels: number,
    templatesDataset: ZarrDataset,
  ) {
    this.#zarrGroup = zarrGroup;
    this.#numTemplates = numTemplates;
    this.#numChannels = numChannels;
    this.#templatesDataset = templatesDataset;
  }

  static async create(zarrGroup: ZarrGroup): Promise<TemplatesViewClient> {
    const attrs = zarrGroup.attrs;

    const numTemplates = attrs["num_templates"] as number;
    const numChannels = attrs["num_channels"] as number;

    if (numTemplates === undefined || numChannels === undefined) {
      throw new Error("Missing required attributes in zarr group");
    }

    // Get the templates dataset
    const templatesDataset = await zarrGroup.getDataset("templates");
    if (!templatesDataset) {
      throw new Error("No templates dataset found");
    }

    const client = new TemplatesViewClient(
      zarrGroup,
      numTemplates,
      numChannels,
      templatesDataset,
    );

    return client;
  }

  get numTemplates(): number {
    return this.#numTemplates;
  }

  get numChannels(): number {
    return this.#numChannels;
  }

  get numUnits(): number {
    return this.#numTemplates;
  }

  get templatesDataset(): ZarrDataset {
    return this.#templatesDataset;
  }

  async getElectrodeCoords(): Promise<number[][]> {
    if (this.#electrodeCoords === null) {
      const coordsDataset =
        await this.#zarrGroup.getDataset("electrode_coords");
      if (!coordsDataset) {
        throw new Error("No electrode_coords dataset found");
      }
      const data = await coordsDataset.getData({});
      const coordsArray = data as Float32Array;
      
      // Convert flat array to array of [x, y] pairs
      this.#electrodeCoords = [];
      for (let i = 0; i < this.#numChannels; i++) {
        this.#electrodeCoords.push([
          coordsArray[i * 2],
          coordsArray[i * 2 + 1],
        ]);
      }
    }
    return this.#electrodeCoords;
  }
}
