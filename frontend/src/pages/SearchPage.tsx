import { useCallback, useRef } from 'react';
import type { SearchParams } from '../types';
import { SearchBar } from '../components/SearchBar';
import { FilterPanel, type FilterPanelHandle } from '../components/FilterPanel';
import { ListingGrid } from '../components/ListingGrid';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useSearch } from '../hooks/useSearch';
import { useFavorites } from '../hooks/useFavorites';

export function SearchPage() {
  const { listings, total, hasMore, loading, searched, search, loadMore, toggleFavorite } = useSearch();
  const { toggle: toggleFav } = useFavorites();
  const queryRef = useRef('');
  const filterRef = useRef<FilterPanelHandle>(null);

  const handleSearch = useCallback((query: string) => {
    queryRef.current = query;
    const currentParams = filterRef.current?.getCurrentParams();
    search(currentParams ? { ...currentParams, q: query } : { q: query, sort_by: 'date', sort_order: 'desc' });
  }, [search]);

  const handleFiltersChange = useCallback((params: SearchParams) => {
    search(params);
  }, [search]);

  const handleToggleFavorite = useCallback(async (itemId: string) => {
    const newState = await toggleFav(itemId);
    toggleFavorite(itemId, newState);
  }, [toggleFav, toggleFavorite]);

  return (
    <div className="flex gap-6 p-6 max-w-screen-2xl mx-auto">
      <aside className="w-72 shrink-0">
        <div className="sticky top-6 bg-gray-800/50 rounded-lg border border-gray-700 p-4">
          <FilterPanel ref={filterRef} onFiltersChange={handleFiltersChange} query={queryRef.current} />
        </div>
      </aside>

      <main className="flex-1 min-w-0">
        <SearchBar onSearch={handleSearch} loading={loading} />

        {searched && !loading && (
          <p className="text-gray-400 text-sm mt-4 mb-4">
            {total.toLocaleString('nl-NL')} results found
          </p>
        )}

        {loading && listings.length === 0 && <LoadingSpinner />}

        {searched && !loading && listings.length === 0 && (
          <div className="text-center py-16">
            <p className="text-gray-400 text-lg">No motorcycles found</p>
            <p className="text-gray-500 text-sm mt-2">Try adjusting your search or filters</p>
          </div>
        )}

        <ListingGrid
          listings={listings}
          hasMore={hasMore}
          loading={loading && listings.length > 0}
          onLoadMore={loadMore}
          onToggleFavorite={handleToggleFavorite}
        />
      </main>
    </div>
  );
}
