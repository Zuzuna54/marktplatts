interface Props {
  label: string;
  unit?: string;
  min?: number;
  max?: number;
  onMinChange: (val: number | undefined) => void;
  onMaxChange: (val: number | undefined) => void;
}

export function RangeInput({ label, unit, min, max, onMinChange, onMaxChange }: Props) {
  return (
    <div className="space-y-1">
      <label className="text-sm text-gray-400">{label}{unit ? ` (${unit})` : ''}</label>
      <div className="flex gap-2">
        <input
          type="number"
          value={min ?? ''}
          onChange={e => onMinChange(e.target.value ? Number(e.target.value) : undefined)}
          placeholder="Min"
          className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
        />
        <input
          type="number"
          value={max ?? ''}
          onChange={e => onMaxChange(e.target.value ? Number(e.target.value) : undefined)}
          placeholder="Max"
          className="w-full bg-gray-800 border border-gray-600 rounded px-2 py-1.5 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
        />
      </div>
    </div>
  );
}
