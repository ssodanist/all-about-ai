export interface AICompany {
  id: string;
  name: string;
  description: string;
  share: number; // Percentage share of the grid (0-100)
  color: string;
  textColor: string;
  domain: string; // Used for fetching logos
  logoUrl?: string; // Constructed URL
  url?: string;
}

export interface GridState {
  companies: AICompany[];
  lastUpdated: string;
  totalBlocks: number;
}

export interface GroundingChunk {
  web?: {
    uri: string;
    title: string;
  };
}

export type GridBlock = {
  id: string;
  companyId: string;
} | null; // Null represents empty space