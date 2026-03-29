import { useState, useCallback, useRef } from 'react';
import type { Listing, SearchParams, SearchResponse } from '../types';
import { searchListings } from '../api/client';

const PAGE_SIZE = 100;

const DEFAULT_PARAMS: SearchParams = {
  q: '',
  sort_by: 'date',
  sort_order: 'desc',
};

export function useSearch() {
  const [params, setParams] = useState<SearchParams>(DEFAULT_PARAMS);
  const [listings, setListings] = useState<Listing[]>([]);
  const [total, setTotal] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const offsetRef = useRef(0);
  const loadingRef = useRef(false);
  const abortRef = useRef<AbortController | null>(null);

  const search = useCallback(async (newParams: SearchParams) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setParams(newParams);
    setListings([]);
    setInitialLoading(true);
    setLoading(true);
    loadingRef.current = true;
    setSearched(true);
    offsetRef.current = 0;

    try {
      const data: SearchResponse = await searchListings(newParams, 0, PAGE_SIZE, controller.signal);
      if (controller.signal.aborted) return;
      setListings(data.listings);
      setTotal(data.total);
      setHasMore(data.has_more);
      offsetRef.current = PAGE_SIZE;
    } catch (e) {
      if (e instanceof DOMException && e.name === 'AbortError') return;
      if (controller.signal.aborted) return;
      console.error('Search failed:', e);
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
        setInitialLoading(false);
        loadingRef.current = false;
      }
    }
  }, []);

  const loadMore = useCallback(async () => {
    if (loadingRef.current || !hasMore) return;
    loadingRef.current = true;
    setLoading(true);

    try {
      const data = await searchListings(params, offsetRef.current, PAGE_SIZE);
      setListings(prev => [...prev, ...data.listings]);
      setHasMore(data.has_more);
      offsetRef.current += PAGE_SIZE;
    } catch (e) {
      console.error('Load more failed:', e);
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  }, [hasMore, params]);

  const toggleFavorite = useCallback((itemId: string, isFavorite: boolean) => {
    setListings(prev =>
      prev.map(l => (l.item_id === itemId ? { ...l, is_favorite: isFavorite } : l))
    );
  }, []);

  return { params, listings, total, hasMore, loading, initialLoading, searched, search, loadMore, toggleFavorite };
}
