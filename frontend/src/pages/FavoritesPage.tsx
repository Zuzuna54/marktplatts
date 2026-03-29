import { useCallback } from 'react';
import { useFavorites } from '../hooks/useFavorites';
import { ListingGrid } from '../components/ListingGrid';
import { LoadingSpinner } from '../components/LoadingSpinner';

export function FavoritesPage() {
  const { favorites, loading, toggle, refetch } = useFavorites();

  const handleToggleFavorite = useCallback(async (itemId: string) => {
    await toggle(itemId);
    refetch();
  }, [toggle, refetch]);

  return (
    <div className="p-6 max-w-screen-2xl mx-auto">
      <h2 className="text-2xl font-bold text-gray-100 mb-6">
        Favorites ({favorites.length})
      </h2>

      {loading && <LoadingSpinner />}

      {!loading && favorites.length === 0 && (
        <div className="text-center py-16">
          <p className="text-gray-400 text-lg">No favorites yet</p>
          <p className="text-gray-500 text-sm mt-2">Search for motorcycles and save your favorites</p>
        </div>
      )}

      <ListingGrid
        listings={favorites}
        hasMore={false}
        loading={false}
        onLoadMore={() => {}}
        onToggleFavorite={handleToggleFavorite}
      />
    </div>
  );
}
