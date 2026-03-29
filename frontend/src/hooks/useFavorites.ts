import { useState, useCallback, useEffect } from 'react';
import type { Listing } from '../types';
import { getFavorites, addFavorite, removeFavorite } from '../api/client';

export function useFavorites() {
  const [favorites, setFavorites] = useState<Listing[]>([]);
  const [favoriteIds, setFavoriteIds] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  const fetchFavorites = useCallback(async () => {
    setLoading(true);
    try {
      const data = await getFavorites();
      setFavorites(data);
      setFavoriteIds(new Set(data.map(l => l.item_id)));
    } catch (e) {
      console.error('Failed to fetch favorites:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchFavorites();
  }, [fetchFavorites]);

  const toggle = useCallback(async (itemId: string) => {
    const isFav = favoriteIds.has(itemId);
    try {
      if (isFav) {
        await removeFavorite(itemId);
        setFavoriteIds(prev => {
          const next = new Set(prev);
          next.delete(itemId);
          return next;
        });
        setFavorites(prev => prev.filter(l => l.item_id !== itemId));
      } else {
        await addFavorite(itemId);
        setFavoriteIds(prev => new Set(prev).add(itemId));
      }
      return !isFav;
    } catch (e) {
      console.error('Failed to toggle favorite:', e);
      return isFav;
    }
  }, [favoriteIds]);

  const isFavorite = useCallback((itemId: string) => favoriteIds.has(itemId), [favoriteIds]);

  return { favorites, favoriteIds, loading, toggle, isFavorite, refetch: fetchFavorites };
}
