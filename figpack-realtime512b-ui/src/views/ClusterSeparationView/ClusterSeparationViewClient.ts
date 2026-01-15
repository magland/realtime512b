import { ZarrGroup } from "../../figpack-interface";

export interface SeparationItem {
  unit_id_1: string;
  unit_id_2: string;
  projections_1: Float32Array;
  projections_2: Float32Array;
}

export class ClusterSeparationViewClient {
  #zarrGroup: ZarrGroup;
  #numItems: number;
  #items: SeparationItem[] | null = null;

  constructor(zarrGroup: ZarrGroup, numItems: number) {
    this.#zarrGroup = zarrGroup;
    this.#numItems = numItems;
  }

  static async create(
    zarrGroup: ZarrGroup
  ): Promise<ClusterSeparationViewClient> {
    const attrs = zarrGroup.attrs;

    const numItems = attrs["num_items"] as number;

    if (numItems === undefined) {
      throw new Error("Missing num_items attribute in zarr group");
    }

    const client = new ClusterSeparationViewClient(zarrGroup, numItems);

    return client;
  }

  get numItems(): number {
    return this.#numItems;
  }

  async getItems(): Promise<SeparationItem[]> {
    if (this.#items === null) {
      this.#items = [];

      // Load consolidated datasets
      const unitIds1Dataset = await this.#zarrGroup.getDataset("unit_ids_1");
      const unitIds2Dataset = await this.#zarrGroup.getDataset("unit_ids_2");
      const projectionStarts1Dataset = await this.#zarrGroup.getDataset("projection_starts_1");
      const projectionStarts2Dataset = await this.#zarrGroup.getDataset("projection_starts_2");
      const projections1Dataset = await this.#zarrGroup.getDataset("projections_1");
      const projections2Dataset = await this.#zarrGroup.getDataset("projections_2");

      if (
        !unitIds1Dataset ||
        !unitIds2Dataset ||
        !projectionStarts1Dataset ||
        !projectionStarts2Dataset ||
        !projections1Dataset ||
        !projections2Dataset
      ) {
        throw new Error("Missing required datasets");
      }

      const unitIds1 = (await unitIds1Dataset.getData({})) as Int32Array;
      const unitIds2 = (await unitIds2Dataset.getData({})) as Int32Array;
      const projectionStarts1 = (await projectionStarts1Dataset.getData({})) as Int32Array;
      const projectionStarts2 = (await projectionStarts2Dataset.getData({})) as Int32Array;
      const allProjections1 = (await projections1Dataset.getData({})) as Float32Array;
      const allProjections2 = (await projections2Dataset.getData({})) as Float32Array;

      // Parse items from consolidated arrays
      for (let i = 0; i < this.#numItems; i++) {
        const unit_id_1 = String(unitIds1[i]);
        const unit_id_2 = String(unitIds2[i]);

        const start1 = projectionStarts1[i];
        const end1 = projectionStarts1[i + 1];
        const start2 = projectionStarts2[i];
        const end2 = projectionStarts2[i + 1];

        const projections_1 = allProjections1.slice(start1, end1);
        const projections_2 = allProjections2.slice(start2, end2);

        this.#items.push({
          unit_id_1,
          unit_id_2,
          projections_1,
          projections_2,
        });
      }
    }

    return this.#items;
  }

  async getItem(index: number): Promise<SeparationItem> {
    const items = await this.getItems();
    if (index < 0 || index >= items.length) {
      throw new Error(`Item index ${index} out of range`);
    }
    return items[index];
  }
}
