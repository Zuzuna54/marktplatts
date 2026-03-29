import { useState, useCallback, useImperativeHandle, forwardRef } from 'react';
import type { SearchParams } from '../types';
import { RangeInput } from './RangeInput';
import { SortControl } from './SortControl';

interface Props {
  onFiltersChange: (params: SearchParams) => void;
  query: string;
}

export interface FilterPanelHandle {
  getCurrentParams: () => SearchParams;
}

export const FilterPanel = forwardRef<FilterPanelHandle, Props>(function FilterPanel({ onFiltersChange, query }, ref) {
  const [priceMin, setPriceMin] = useState<number | undefined>();
  const [priceMax, setPriceMax] = useState<number | undefined>();
  const [mileageMin, setMileageMin] = useState<number | undefined>();
  const [mileageMax, setMileageMax] = useState<number | undefined>();
  const [engineMin, setEngineMin] = useState<number | undefined>();
  const [engineMax, setEngineMax] = useState<number | undefined>();
  const [yearMin, setYearMin] = useState<number | undefined>();
  const [yearMax, setYearMax] = useState<number | undefined>();
  const [datePosted, setDatePosted] = useState('');
  const [source, setSource] = useState('');
  const [sortBy, setSortBy] = useState('date');
  const [sortOrder, setSortOrder] = useState('desc');

  const buildParams = useCallback((q: string): SearchParams => ({
    q,
    price_min: priceMin,
    price_max: priceMax,
    mileage_min: mileageMin,
    mileage_max: mileageMax,
    engine_min: engineMin,
    engine_max: engineMax,
    year_min: yearMin,
    year_max: yearMax,
    date_posted: datePosted || undefined,
    source: source || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
  }), [priceMin, priceMax, mileageMin, mileageMax, engineMin, engineMax, yearMin, yearMax, datePosted, source, sortBy, sortOrder]);

  useImperativeHandle(ref, () => ({
    getCurrentParams: () => buildParams(query),
  }), [buildParams, query]);

  const handleApply = () => {
    onFiltersChange(buildParams(query));
  };

  const handleClear = () => {
    setPriceMin(undefined);
    setPriceMax(undefined);
    setMileageMin(undefined);
    setMileageMax(undefined);
    setEngineMin(undefined);
    setEngineMax(undefined);
    setYearMin(undefined);
    setYearMax(undefined);
    setDatePosted('');
    setSource('');
    setSortBy('date');
    setSortOrder('desc');
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wide">Filters</h3>
        <button onClick={handleClear} className="text-xs text-blue-400 hover:text-blue-300">
          Clear all
        </button>
      </div>

      <RangeInput label="Price" unit="EUR" min={priceMin} max={priceMax} onMinChange={setPriceMin} onMaxChange={setPriceMax} />
      <RangeInput label="Mileage" unit="km" min={mileageMin} max={mileageMax} onMinChange={setMileageMin} onMaxChange={setMileageMax} />
      <RangeInput label="Engine size" unit="cc" min={engineMin} max={engineMax} onMinChange={setEngineMin} onMaxChange={setEngineMax} />
      <RangeInput label="Year" min={yearMin} max={yearMax} onMinChange={setYearMin} onMaxChange={setYearMax} />

      <div className="space-y-1">
        <label className="text-sm text-gray-400">Date posted</label>
        <select
          value={datePosted}
          onChange={e => setDatePosted(e.target.value)}
          className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
        >
          <option value="">All time</option>
          <option value="1d">Last 24 hours</option>
          <option value="7d">Last 7 days</option>
          <option value="30d">Last 30 days</option>
        </select>
      </div>

      <div className="space-y-1">
        <label className="text-sm text-gray-400">Source</label>
        <select
          value={source}
          onChange={e => setSource(e.target.value)}
          className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
        >
          <option value="">All sources</option>
          <option value="marktplaats">Marktplaats</option>
          <option value="autoscout24">AutoScout24</option>
          <option value="2dehands">2dehands.be</option>
          <option value="motoroccasion">Motoroccasion.nl</option>
          <option value="bva">BVA Auctions</option>
          <option value="catawiki">Catawiki</option>
        </select>
      </div>

      <hr className="border-gray-700" />

      <SortControl
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSortByChange={setSortBy}
        onSortOrderChange={setSortOrder}
      />

      <button
        onClick={handleApply}
        className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 rounded-lg font-medium transition-colors"
      >
        Apply Filters
      </button>
    </div>
  );
});
