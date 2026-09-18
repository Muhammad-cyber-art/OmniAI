import { useState } from 'react';

const EMOJI_MAP = {
  // Direct emoji symbols
  '👋': '1f44b',
  '🎮': '1f3ae',
  '📚': '1f4da',
  '👥': '1f465',
  '🚀': '1f680',
  '📝': '1f4dd',
  '🤖': '1f916',
  '📊': '1f4ca',
  '⚡': '26a1',
  '🎭': '1f3ad',
  '🔗': '1f517',
  '🏆': '1f3c6',
  '🎓': '1f393',
  '👨‍🏫': '1f468-200d-1f3eb',
  '🏛️': '1f3db-fe0f',
  '🏛': '1f3db-fe0f',
  '🎯': '1f3af',
  '🔥': '1f525',
  '⚖️': '2696-fe0f',
  '⚖': '2696-fe0f',
  '🛡️': '1f6e1-fe0f',
  '🛡': '1f6e1-fe0f',
  '🔨': '1f528',
  '⭐': '2b50',
  '✨': '2728',
  '💡': '1f4a1',
  '🔒': '1f512',
  '💻': '1f4bb',

  // Aliases / names
  wave: '1f44b',
  game: '1f3ae',
  books: '1f4da',
  people: '1f465',
  rocket: '1f680',
  memo: '1f4dd',
  robot: '1f916',
  chart: '1f4ca',
  zap: '26a1',
  theater: '1f3ad',
  link: '1f517',
  trophy: '1f3c6',
  grad: '1f393',
  teacher: '1f468-200d-1f3eb',
  court: '1f3db-fe0f',
  target: '1f3af',
  fire: '1f525',
  balance: '2696-fe0f',
  shield: '1f6e1-fe0f',
  hammer: '1f528',
  star: '2b50',
  sparkles: '2728',
  idea: '1f4a1',
  lock: '1f512',
  laptop: '1f4bb',
};

function resolveEmojiCode(input) {
  if (!input) return null;
  const str = String(input).trim();
  if (EMOJI_MAP[str]) return EMOJI_MAP[str];

  try {
    const points = [...str].map((c) => c.codePointAt(0).toString(16));
    const cleanPoints = points.filter((p) => p !== 'fe0f');
    return cleanPoints.join('-');
  } catch {
    return null;
  }
}

/**
 * AppleSticker component renders official Apple iOS / iPhone style emoji stickers.
 * It uses local high-resolution Apple emoji assets with automatic fallback to CDN.
 */
export default function AppleSticker({
  symbol,
  name,
  children,
  size = 24,
  className = '',
  alt,
}) {
  const target = symbol || name || children;
  const code = resolveEmojiCode(target);
  const [srcIndex, setSrcIndex] = useState(0);

  if (!code) {
    return <span className={className}>{target}</span>;
  }

  const isNumberSize = typeof size === 'number';
  const style = isNumberSize
    ? { width: `${size}px`, height: `${size}px` }
    : {};
  const sizeClass = !isNumberSize ? size : '';

  const sources = [
    `/stickers/${code}.png`,
    `https://cdn.jsdelivr.net/npm/emoji-datasource-apple@15.1.2/img/apple/64/${code}.png`,
  ];

  if (srcIndex >= sources.length) {
    return <span className={className}>{target}</span>;
  }

  return (
    <img
      src={sources[srcIndex]}
      alt={alt || (typeof target === 'string' ? target : 'sticker')}
      style={style}
      loading="lazy"
      onError={() => setSrcIndex((prev) => prev + 1)}
      className={`inline-block select-none pointer-events-none object-contain align-middle ${sizeClass} ${className}`}
      draggable={false}
    />
  );
}
