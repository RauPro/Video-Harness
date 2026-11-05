import React, {useMemo} from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {font} from './fonts';
import type {Caption, Props} from './types';
import {POSITION_Y, isMoney, normWord, outline} from './util';

type Page = {startMs: number; endMs: number; words: Caption[]};

export const paginate = (words: Caption[], maxWords: number, pauseMs = 320): Page[] => {
  const pages: Page[] = [];
  let cur: Caption[] = [];
  const flush = () => {
    if (cur.length) pages.push({startMs: cur[0].startMs, endMs: cur[cur.length - 1].endMs, words: cur});
    cur = [];
  };
  words.forEach((w, i) => {
    cur.push(w);
    const next = words[i + 1];
    const endsClause = /[.,!?;:…]$/.test(w.text.trim());
    if (!next || cur.length >= maxWords || endsClause || next.startMs - w.endMs > pauseMs) flush();
  });
  // Hold each page until the next one starts (no flicker between words).
  for (let i = 0; i < pages.length - 1; i++) {
    const gap = pages[i + 1].startMs - pages[i].endMs;
    if (gap < 700) pages[i].endMs = pages[i + 1].startMs;
  }
  return pages;
};

export const CaptionsLayer: React.FC<{props: Props}> = ({props}) => {
  const {timeline, theme, captions} = props;
  const frame = useCurrentFrame();
  const {fps, width} = useVideoConfig();
  const cfg = {...theme.captions, ...Object.fromEntries(Object.entries(timeline.captions ?? {}).filter(([, v]) => v != null))};
  const preset = cfg.preset ?? theme.captions.preset;
  const maxWords = cfg.maxWords ?? theme.captions.maxWords;
  const pages = useMemo(() => paginate(captions, maxWords), [captions, maxWords]);
  if (preset === 'none' || !captions.length) return null;

  const ms = (frame / fps) * 1000;
  const t = frame / fps;
  const hidden = (timeline.captions?.hideDuring ?? []).some(([a, b]) => t >= a && t < b) ||
    timeline.overlays.some((o) => o.type === 'questionCard' && t >= o.start && t < o.start + o.duration);
  const page = pages.find((p) => ms >= p.startMs && ms < p.endMs);
  if (hidden || !page) return null;

  const highlights = new Set((timeline.captions?.highlight ?? []).map(normWord));
  const pageFrame = frame - Math.round((page.startMs / 1000) * fps);
  const scale = width / 1080;
  const size = (cfg.size ?? 90) * scale;
  const upper = cfg.uppercase ?? theme.captions.uppercase;
  const top = POSITION_Y[(cfg.position ?? theme.captions.position) as keyof typeof POSITION_Y] * 100;

  const colorFor = (w: Caption, active: boolean) => {
    const n = normWord(w.text);
    if (highlights.has(n)) return theme.colors.highlight;
    if (isMoney(w.text)) return theme.colors.money;
    if (preset === 'karaoke' && active) return theme.colors.highlight;
    return theme.colors.text;
  };

  if (preset === 'subtle') {
    const opacity = interpolate(pageFrame, [0, 4], [0, 1], {extrapolateRight: 'clamp'});
    return (
      <AbsoluteFill style={{alignItems: 'center'}}>
        <div style={{position: 'absolute', top: `${top}%`, transform: 'translateY(-50%)', width: '86%', textAlign: 'center',
          fontFamily: font(theme.fonts.caption), fontWeight: theme.fonts.captionWeight, fontSize: size, lineHeight: 1.2,
          color: theme.colors.text, textShadow: outline(cfg.strokeWidth ?? 0, theme.colors.stroke), opacity,
          textTransform: upper ? 'uppercase' : 'none', letterSpacing: upper ? '0.02em' : 0}}>
          {page.words.map((w, i) => <span key={i} style={{color: colorFor(w, false)}}>{w.text}</span>)}
        </div>
      </AbsoluteFill>
    );
  }

  const pop = spring({frame: pageFrame, fps, config: {damping: 12, stiffness: 220, mass: 0.6}});
  return (
    <AbsoluteFill style={{alignItems: 'center'}}>
      <div style={{position: 'absolute', top: `${top}%`, transform: `translateY(-50%) scale(${interpolate(pop, [0, 1], [0.7, 1])})`,
        width: '88%', display: 'flex', flexWrap: 'wrap', justifyContent: 'center', columnGap: size * 0.28, rowGap: 0,
        fontFamily: font(theme.fonts.caption), fontWeight: theme.fonts.captionWeight, fontSize: size, lineHeight: 1.08,
        textTransform: upper ? 'uppercase' : 'none', textAlign: 'center'}}>
        {page.words.map((w, i) => {
          const active = ms >= w.startMs && ms < w.endMs + 80;
          const spoken = ms >= w.startMs - 40;
          const wordPop = preset === 'karaoke' && active ? 1.08 : 1;
          return (
            <span key={i} style={{color: colorFor(w, active), opacity: preset === 'karaoke' || spoken ? 1 : 0,
              transform: `scale(${wordPop})`, textShadow: outline((cfg.strokeWidth ?? 7) * scale, theme.colors.stroke)}}>
              {w.text.trim()}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
