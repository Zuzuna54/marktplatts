interface Props {
  isFavorite: boolean;
  onClick: () => void;
}

export function FavoriteBadge({ isFavorite, onClick }: Props) {
  return (
    <button
      onClick={e => {
        e.preventDefault();
        e.stopPropagation();
        onClick();
      }}
      className="p-1.5 rounded-full hover:bg-gray-700/50 transition-colors"
      title={isFavorite ? 'Remove from favorites' : 'Add to favorites'}
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill={isFavorite ? '#ef4444' : 'none'}
        stroke={isFavorite ? '#ef4444' : '#9ca3af'}
        strokeWidth={2}
        className="w-5 h-5"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M21 8.25c0-2.485-2.099-4.5-4.688-4.5-1.935 0-3.597 1.126-4.312 2.733-.715-1.607-2.377-2.733-4.313-2.733C5.1 3.75 3 5.765 3 8.25c0 7.22 9 12 9 12s9-4.78 9-12z"
        />
      </svg>
    </button>
  );
}
