import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {AudioTracks} from './AudioTracks';
import {CaptionsLayer} from './Captions';
import {OverlayView} from './overlays';
import {HANDLE_SECONDS, OVERLAP, Shot} from './Shot';
import type {Props} from './types';

export const Main: React.FC<Props> = (props) => {
  const {timeline} = props;
  const {fps} = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  // Inserts are cutaways: captions keep playing on top of them. Every other overlay draws above the captions.
  const overlays = (inserts: boolean) =>
    timeline.overlays.map((o, i) =>
      (o.type === 'imageInsert') === inserts && (
        <Sequence key={i} from={f(o.start)} durationInFrames={Math.max(1, f(o.start + o.duration) - f(o.start))}
          name={`${o.type} ${i}`}>
          <OverlayView overlay={o} theme={props.theme} />
        </Sequence>
      ));
  const shots = [...timeline.video].sort((a, b) => a.start - b.start);
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {shots.map((clip, i) => {
        const next = shots[i + 1];
        const tail = next?.transitionIn && OVERLAP.has(next.transitionIn.type)
          ? f(Math.min(next.transitionIn.duration, clip.tailMax ?? HANDLE_SECONDS)) : 0;
        return (
          <Sequence
            key={clip.id}
            from={f(clip.start)}
            durationInFrames={Math.max(1, f(clip.start + clip.duration) - f(clip.start) + tail)}
            name={`shot ${clip.id}`}
          >
            <Shot clip={clip} />
          </Sequence>
        );
      })}
      {overlays(true)}
      <CaptionsLayer props={props} />
      {overlays(false)}
      <AudioTracks props={props} />
    </AbsoluteFill>
  );
};
