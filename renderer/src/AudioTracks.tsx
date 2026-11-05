import React from 'react';
import {Audio, Sequence, interpolate, staticFile, useVideoConfig} from 'remotion';
import type {Props} from './types';

/** 0..1 amount of ducking at time ms, with 200 ms ramps around speech regions. */
const duckAmount = (ms: number, speech: [number, number][], ramp = 200): number => {
  let d = 0;
  for (const [a, b] of speech) {
    if (ms < a - ramp || ms > b + ramp) continue;
    d = Math.max(d, interpolate(ms, [a - ramp, a, b, b + ramp], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}));
    if (d === 1) break;
  }
  return d;
};

export const AudioTracks: React.FC<{props: Props}> = ({props}) => {
  const {timeline, speech} = props;
  const {fps, durationInFrames} = useVideoConfig();
  const vo = timeline.voiceover;
  const music = timeline.music;
  return (
    <>
      {vo && (
        <Sequence from={Math.round(vo.start * fps)} name="voiceover">
          <Audio src={staticFile(vo.src)} volume={vo.volume} />
        </Sequence>
      )}
      {music && (
        <Sequence from={Math.round(music.start * fps)} name="music">
          <Audio
            src={staticFile(music.src)}
            startFrom={Math.round(music.sourceIn * fps)}
            loop
            volume={(f) => {
              const abs = f + Math.round(music.start * fps);
              const ms = (abs / fps) * 1000;
              const fadeIn = music.fadeIn > 0 ? Math.min(1, f / (music.fadeIn * fps)) : 1;
              const fadeOut = music.fadeOut > 0 ? Math.min(1, (durationInFrames - abs) / (music.fadeOut * fps)) : 1;
              const level = interpolate(duckAmount(ms, speech), [0, 1], [music.volume, music.duckTo]);
              return Math.max(0, level * fadeIn * fadeOut);
            }}
          />
        </Sequence>
      )}
      {timeline.sfx.map((s, i) => (
        <Sequence key={i} from={Math.round(s.start * fps)} name={`sfx ${s.src}`}>
          <Audio src={staticFile(s.src)} volume={s.volume} />
        </Sequence>
      ))}
    </>
  );
};
