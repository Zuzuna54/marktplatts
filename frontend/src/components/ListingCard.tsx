import type { Listing } from '../types';
import { FavoriteBadge } from './FavoriteBadge';
import { ImageViewer } from './ImageViewer';

interface Props {
  listing: Listing;
  onToggleFavorite: (itemId: string) => void;
}

function formatPrice(cents: number | null, priceType: string | null): string {
  if (cents != null && cents > 0) {
    return `\u20AC ${(cents / 100).toLocaleString('nl-NL', { minimumFractionDigits: 0 })}`;
  }
  if (priceType === 'FAST_BID' || priceType === 'MIN_BID') return 'Bieden';
  if (priceType === 'SEE_DESCRIPTION') return 'Zie omschrijving';
  if (priceType === 'NOTK') return 'N.o.t.k.';
  if (priceType === 'FREE') return 'Gratis';
  if (priceType === 'EXCHANGE') return 'Ruilen';
  return 'Prijs onbekend';
}

function formatDate(dateStr: string | null): string {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffDays = Math.floor(diffMs / 86400000);
  if (diffDays === 0) return 'Vandaag';
  if (diffDays === 1) return 'Gisteren';
  if (diffDays < 7) return `${diffDays} dagen geleden`;
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weken geleden`;
  return d.toLocaleDateString('nl-NL');
}

const SOURCE_COLORS: Record<string, string> = {
  marktplaats: 'bg-orange-600',
  autoscout24: 'bg-blue-600',
  '2dehands': 'bg-green-600',
  motoroccasion: 'bg-purple-600',
  bva: 'bg-red-600',
  catawiki: 'bg-yellow-600',
};

const SOURCE_LABELS: Record<string, string> = {
  marktplaats: 'MP',
  autoscout24: 'AS24',
  '2dehands': '2DH',
  motoroccasion: 'MO',
  bva: 'BVA',
  catawiki: 'CW',
};

function formatTimeRemaining(endTime: string | null): string {
  if (!endTime) return '';
  const end = new Date(endTime);
  const now = new Date();
  const diffMs = end.getTime() - now.getTime();
  if (diffMs <= 0) return 'Ended';
  const hours = Math.floor(diffMs / 3600000);
  const mins = Math.floor((diffMs % 3600000) / 60000);
  if (hours > 24) return `${Math.floor(hours / 24)}d ${hours % 24}h`;
  return `${hours}h ${mins}m`;
}

function truncate(s: string | null, len: number): string {
  if (!s) return '';
  return s.length > len ? s.slice(0, len) + '...' : s;
}

export function ListingCard({ listing, onToggleFavorite }: Props) {
  const badges: string[] = [];
  if (listing.construction_year) badges.push(`${listing.construction_year}`);
  if (listing.mileage_km != null) badges.push(`${listing.mileage_km.toLocaleString('nl-NL')} km`);
  if (listing.engine_cc != null) badges.push(`${listing.engine_cc} cc`);
  if (listing.cylinders != null) badges.push(`${listing.cylinders} cyl`);

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-gray-500 transition-colors">
      <a href={listing.link} target="_blank" rel="noopener noreferrer" className="block">
        <div className="relative">
          <ImageViewer
            images={listing.images.length > 0 ? listing.images : (listing.thumbnail_url ? [{ medium: listing.thumbnail_url, large: listing.thumbnail_url }] : [])}
            alt={listing.title}
          />
          <div className="absolute top-2 left-2 z-10">
            <span className={`text-white text-xs font-bold px-1.5 py-0.5 rounded ${SOURCE_COLORS[listing.source] || 'bg-gray-600'}`}>
              {SOURCE_LABELS[listing.source] || listing.source}
            </span>
          </div>
          <div className="absolute top-2 right-2 z-10">
            <FavoriteBadge
              isFavorite={listing.is_favorite}
              onClick={() => onToggleFavorite(listing.item_id)}
            />
          </div>
        </div>

        <div className="p-4 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <h3 className="text-gray-100 font-medium text-sm leading-tight line-clamp-2">
              {listing.title}
            </h3>
          </div>

          <div className="text-lg font-bold text-blue-400">
            {listing.is_auction && listing.current_bid_cents
              ? `\u20AC ${(listing.current_bid_cents / 100).toLocaleString('nl-NL')} (bid)`
              : formatPrice(listing.price_cents, listing.price_type)}
          </div>

          {listing.is_auction && (
            <div className="flex items-center gap-2 text-xs">
              <span className="bg-red-900/50 text-red-300 px-1.5 py-0.5 rounded">Auction</span>
              {listing.auction_end_time && (
                <span className="text-gray-400">{formatTimeRemaining(listing.auction_end_time)}</span>
              )}
              {listing.bid_count != null && (
                <span className="text-gray-400">{listing.bid_count} bids</span>
              )}
            </div>
          )}

          {badges.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {badges.map((b, i) => (
                <span key={i} className="bg-gray-700 text-gray-300 text-xs px-2 py-0.5 rounded">
                  {b}
                </span>
              ))}
            </div>
          )}

          <p className="text-gray-400 text-xs leading-relaxed">
            {truncate(listing.description, 100)}
          </p>

          <div className="flex items-center justify-between text-xs text-gray-500 pt-1">
            <div className="flex items-center gap-2">
              {listing.city && <span>{listing.city}</span>}
              {listing.distance_km != null && (
                <span>({Math.round(listing.distance_km)} km)</span>
              )}
            </div>
            <span>{formatDate(listing.post_date)}</span>
          </div>

          <div className="flex items-center gap-2 pt-1">
            {listing.advertiser_type && (
              <span className={`text-xs px-2 py-0.5 rounded ${
                listing.advertiser_type === 'Bedrijf'
                  ? 'bg-amber-900/50 text-amber-300'
                  : 'bg-gray-700 text-gray-400'
              }`}>
                {listing.advertiser_type}
              </span>
            )}
            {listing.condition && (
              <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">
                {listing.condition}
              </span>
            )}
            {listing.motorcycle_type && (
              <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">
                {listing.motorcycle_type}
              </span>
            )}
          </div>
        </div>
      </a>
    </div>
  );
}
