import React from 'react';
import {AbsoluteFill, Easing, OffthreadVideo, interpolate, random, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {VideoClip} from './types';

const GRADES: Record<VideoClip['grade'], string> = {
  none: 'none',
  warm: 'sepia(0.14) saturate(1.18) hue-rotate(-6deg) contrast(1.04)',
  cool: 'saturate(1.05) hue-rotate(8deg) brightness(1.02)',
  vivid: 'saturate(1.35) contrast(1.08)',
  bw: 'grayscale(1) contrast(1.12)',
  film: 'contrast(1.1) saturate(0.88) sepia(0.12)',
};

// Transitions that reveal the outgoing shot, which Main keeps playing underneath.
export const OVERLAP = new Set(['whip', 'slide', 'fade', 'zoom']);
// Conform adds this much footage after each shot (vh/conform.py HANDLE).
export const HANDLE_SECONDS = 0.25;

const DIR: Record<string, [number, number]> = {left: [1, 0], right: [-1, 0], up: [0, 1], down: [0, -1]};

export const Shot: React.FC<{clip: VideoClip}> = ({clip}) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const total = Math.max(1, Math.round(clip.duration * fps));

  // Ken Burns zoom and jump-cut punch-ins.
  const z = clip.zoom;
  let scale = z ? interpolate(frame, [0, total], [z.start, z.end], {extrapolateRight: 'clamp'}) : 1;
  for (const p of clip.punchIns) {
    const pf = Math.round(p * fps);
    scale *= interpolate(frame, [pf, pf + 2], [1, clip.punchScale], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  }
  const origin = `${(z?.focusX ?? 0.5) * 100}% ${(z?.focusY ?? 0.5) * 100}%`;

  // Transition-in effects (applied to the incoming shot).
  const t = clip.transitionIn;
  let transform = `scale(${scale})`;
  let filter = GRADES[clip.grade];
  let opacity = 1;
  let flash = 0;
  let glitch: React.ReactNode = null;
  if (t && t.type !== 'cut') {
    const tf = Math.max(2, Math.round(t.duration * fps));
    const p = interpolate(frame, [0, tf], [0, 1], {extrapolateRight: 'clamp', easing: Easing.out(Easing.cubic)});
    const [dx, dy] = DIR[t.direction] ?? [1, 0];
    if (t.type === 'whip' || t.type === 'slide') {
      transform = `translate(${dx * (1 - p) * width}px, ${dy * (1 - p) * height}px) ${transform}`;
      if (t.type === 'whip') filter = `${filter === 'none' ? '' : filter} blur(${(1 - p) * 40}px)`.trim();
    } else if (t.type === 'zoom') {
      transform = `scale(${interpolate(p, [0, 1], [1.45, 1])}) ${transform}`;
      filter = `${filter === 'none' ? '' : filter} blur(${(1 - p) * 18}px)`.trim();
    } else if (t.type === 'fade') {
      opacity = p;
    } else if (t.type === 'flash') {
      flash = 1 - p;
    } else if (t.type === 'glitch' && frame < tf) {
      const j = (s: string) => (random(`${clip.id}-${frame}-${s}`) - 0.5) * 80 * (1 - p);
      transform = `translate(${j('x')}px, ${j('y') / 4}px) ${transform}`;
      filter = `${filter === 'none' ? '' : filter} hue-rotate(${j('h') * 3}deg) saturate(2)`.trim();
      glitch = [0, 1, 2, 3].map((i) => (
        <div key={i} style={{position: 'absolute', left: 0, right: 0, top: `${random(`${clip.id}-${frame}-b${i}`) * 100}%`,
          height: 8 + random(`${clip.id}-${frame}-h${i}`) * 40, background: i % 2 ? 'rgba(255,0,80,0.35)' : 'rgba(0,255,255,0.35)',
          mixBlendMode: 'screen'}} />
      ));
    }
  }

  return (
    <AbsoluteFill style={{overflow: 'hidden', backgroundColor: t && OVERLAP.has(t.type) ? 'transparent' : 'black'}}>
      <AbsoluteFill style={{transform, transformOrigin: origin, filter, opacity}}>
        <OffthreadVideo
          src={staticFile(clip.src)}
          startFrom={Math.round((clip.srcIn ?? 0) * fps)}
          volume={clip.volume}
          muted={clip.volume === 0}
          style={{width: '100%', height: '100%', objectFit: 'cover'}}
          pauseWhenBuffering
        />
      </AbsoluteFill>
      {glitch}
      {flash > 0 && <AbsoluteFill style={{backgroundColor: t?.color ?? '#fff', opacity: flash}} />}
    </AbsoluteFill>
  );
};
