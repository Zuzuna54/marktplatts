import { useState } from 'react';
import type { ListingImage } from '../types';

interface Props {
  images: ListingImage[];
  alt: string;
}

export function ImageViewer({ images, alt }: Props) {
  const [index, setIndex] = useState(0);
  const [hovered, setHovered] = useState(false);

  if (images.length === 0) {
    return (
      <div className="w-full h-48 bg-gray-700 flex items-center justify-center text-gray-500">
        No image
      </div>
    );
  }

  const current = images[index];
  const hasPrev = index > 0;
  const hasNext = index < images.length - 1;

  return (
    <div
      className="relative w-full h-48"
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      <img
        src={current.large}
        alt={alt}
        className="w-full h-48 object-cover bg-gray-700"
        loading="lazy"
      />

      {hovered && images.length > 1 && (
        <>
          {hasPrev && (
            <button
              onClick={e => { e.preventDefault(); e.stopPropagation(); setIndex(i => i - 1); }}
              className="absolute left-1 top-1/2 -translate-y-1/2 bg-black/60 hover:bg-black/80 text-white w-8 h-8 rounded-full flex items-center justify-center transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z" clipRule="evenodd" />
              </svg>
            </button>
          )}
          {hasNext && (
            <button
              onClick={e => { e.preventDefault(); e.stopPropagation(); setIndex(i => i + 1); }}
              className="absolute right-1 top-1/2 -translate-y-1/2 bg-black/60 hover:bg-black/80 text-white w-8 h-8 rounded-full flex items-center justify-center transition-colors"
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
                <path fillRule="evenodd" d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z" clipRule="evenodd" />
              </svg>
            </button>
          )}
        </>
      )}

      {images.length > 1 && (
        <span className="absolute bottom-1.5 right-1.5 bg-black/70 text-white text-xs px-1.5 py-0.5 rounded">
          {index + 1}/{images.length}
        </span>
      )}
    </div>
  );
}
