interface Props {
  sortBy: string;
  sortOrder: string;
  onSortByChange: (val: string) => void;
  onSortOrderChange: (val: string) => void;
}

const SORT_OPTIONS = [
  { value: 'date', label: 'Date posted' },
  { value: 'price', label: 'Price' },
  { value: 'mileage', label: 'Mileage' },
  { value: 'year', label: 'Year' },
  { value: 'engine', label: 'Engine size' },
];

export function SortControl({ sortBy, sortOrder, onSortByChange, onSortOrderChange }: Props) {
  return (
    <div className="space-y-1">
      <label className="text-sm text-gray-400">Sort by</label>
      <div className="flex gap-2">
        <select
          value={sortBy}
          onChange={e => onSortByChange(e.target.value)}
          className="flex-1 bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
        >
          {SORT_OPTIONS.map(o => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
        <button
          onClick={() => onSortOrderChange(sortOrder === 'desc' ? 'asc' : 'desc')}
          className="bg-gray-800 border border-gray-600 rounded px-3 py-1.5 text-sm text-gray-200 hover:bg-gray-700 transition-colors"
          title={sortOrder === 'desc' ? 'Descending' : 'Ascending'}
        >
          {sortOrder === 'desc' ? '\u2193' : '\u2191'}
        </button>
      </div>
    </div>
  );
}
