import { useEffect, useRef } from 'react';
import type { Listing } from '../types';
import { ListingCard } from './ListingCard';
import { LoadingSpinner } from './LoadingSpinner';

interface Props {
  listings: Listing[];
  hasMore: boolean;
  loading: boolean;
  onLoadMore: () => void;
  onToggleFavorite: (itemId: string) => void;
}

export function ListingGrid({ listings, hasMore, loading, onLoadMore, onToggleFavorite }: Props) {
  const sentinelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loading) {
          onLoadMore();
        }
      },
      { rootMargin: '200px' }
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, loading, onLoadMore]);

  if (listings.length === 0 && !loading) {
    return null;
  }

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {listings.map(listing => (
          <ListingCard
            key={listing.item_id}
            listing={listing}
            onToggleFavorite={onToggleFavorite}
          />
        ))}
      </div>
      <div ref={sentinelRef} />
      {loading && <LoadingSpinner />}
    </div>
  );
}
