import type {Position} from './types';

export const POSITION_Y: Record<Position, number> = {top: 0.12, upper: 0.26, center: 0.5, lower: 0.68, bottom: 0.82};

/** Text outline that renders reliably in headless Chrome (layered shadows). */
export const outline = (width: number, color = '#000'): string => {
  if (width <= 0) return '0 4px 18px rgba(0,0,0,0.55)';
  const shadows: string[] = [];
  const steps = 16;
  for (let i = 0; i < steps; i++) {
    const a = (i / steps) * Math.PI * 2;
    shadows.push(`${(Math.cos(a) * width).toFixed(1)}px ${(Math.sin(a) * width).toFixed(1)}px 0 ${color}`);
  }
  shadows.push(`0 ${width * 1.2}px ${width * 2}px rgba(0,0,0,0.45)`);
  return shadows.join(',');
};

export const normWord = (w: string): string =>
  w.toLowerCase().normalize('NFKD').replace(/[\u0300-\u036f]/g, '').replace(/[^\p{L}\p{N}$%]/gu, '');

export const isMoney = (w: string): boolean => /[$€£฿]|\d+\s?(usd|thb|baht|eur|k)\b|^\d[\d.,]*$/i.test(w.trim());
