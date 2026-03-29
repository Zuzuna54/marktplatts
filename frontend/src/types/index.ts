export interface ListingImage {
  medium: string;
  large: string;
}

export interface Listing {
  item_id: string;
  title: string;
  description: string | null;
  price_cents: number | null;
  price_type: string | null;
  construction_year: number | null;
  mileage_km: number | null;
  engine_cc: number | null;
  cylinders: number | null;
  condition: string | null;
  motorcycle_type: string | null;
  brand: string | null;
  engine_power: string | null;
  advertiser_type: string | null;
  city: string | null;
  distance_km: number | null;
  thumbnail_url: string | null;
  link: string;
  post_date: string | null;
  is_favorite: boolean;
  images: ListingImage[];
  source: string;
  is_auction: boolean;
  current_bid_cents: number | null;
  auction_end_time: string | null;
  bid_count: number | null;
}

export interface SearchParams {
  q: string;
  price_min?: number;
  price_max?: number;
  mileage_min?: number;
  mileage_max?: number;
  engine_min?: number;
  engine_max?: number;
  year_min?: number;
  year_max?: number;
  date_posted?: string;
  source?: string;
  sort_by: string;
  sort_order: string;
}

export interface SearchResponse {
  listings: Listing[];
  total: number;
  has_more: boolean;
}

export interface SyncStatus {
  status: string;
  sync_type: string | null;
  total_in_db: number;
  last_completed: string | null;
  progress_pct: number | null;
  current_source: string | null;
}
