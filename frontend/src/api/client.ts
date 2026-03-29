import type { SearchParams, SearchResponse, Listing, SyncStatus } from '../types';

const BASE = '/api';

function buildSearchUrl(params: SearchParams, offset: number, limit: number): string {
  const sp = new URLSearchParams();
  if (params.q) sp.set('q', params.q);
  if (params.price_min != null) sp.set('price_min', String(params.price_min));
  if (params.price_max != null) sp.set('price_max', String(params.price_max));
  if (params.mileage_min != null) sp.set('mileage_min', String(params.mileage_min));
  if (params.mileage_max != null) sp.set('mileage_max', String(params.mileage_max));
  if (params.engine_min != null) sp.set('engine_min', String(params.engine_min));
  if (params.engine_max != null) sp.set('engine_max', String(params.engine_max));
  if (params.year_min != null) sp.set('year_min', String(params.year_min));
  if (params.year_max != null) sp.set('year_max', String(params.year_max));
  if (params.date_posted) sp.set('date_posted', params.date_posted);
  if (params.source) sp.set('source', params.source);
  sp.set('sort_by', params.sort_by);
  sp.set('sort_order', params.sort_order);
  sp.set('offset', String(offset));
  sp.set('limit', String(limit));
  return `${BASE}/search?${sp.toString()}`;
}

export async function searchListings(
  params: SearchParams,
  offset: number = 0,
  limit: number = 100,
  signal?: AbortSignal,
): Promise<SearchResponse> {
  const res = await fetch(buildSearchUrl(params, offset, limit), { signal });
  if (!res.ok) throw new Error(`Search failed: ${res.status}`);
  return res.json();
}

export async function getFavorites(): Promise<Listing[]> {
  const res = await fetch(`${BASE}/favorites`);
  if (!res.ok) throw new Error(`Failed to get favorites: ${res.status}`);
  return res.json();
}

export async function addFavorite(itemId: string): Promise<void> {
  const res = await fetch(`${BASE}/favorites/${itemId}`, { method: 'POST' });
  if (!res.ok) throw new Error(`Failed to add favorite: ${res.status}`);
}

export async function removeFavorite(itemId: string): Promise<void> {
  const res = await fetch(`${BASE}/favorites/${itemId}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`Failed to remove favorite: ${res.status}`);
}

export async function getSyncStatus(): Promise<SyncStatus> {
  const res = await fetch(`${BASE}/sync/status`);
  if (!res.ok) throw new Error(`Failed to get sync status: ${res.status}`);
  return res.json();
}
