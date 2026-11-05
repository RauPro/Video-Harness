import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {AudioTracks} from './AudioTracks';
import {CaptionsLayer} from './Captions';
import {OverlayView} from './overlays';
import {Shot} from './Shot';
import type {Props} from './types';

export const Main: React.FC<Props> = (props) => {
  const {timeline} = props;
  const {fps} = useVideoConfig();
  const f = (s: number) => Math.round(s * fps);
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {timeline.video.map((clip) => (
        <Sequence key={clip.id} from={f(clip.start)} durationInFrames={Math.max(1, f(clip.start + clip.duration) - f(clip.start))}
          name={`shot ${clip.id}`}>
          <Shot clip={clip} />
        </Sequence>
      ))}
      <CaptionsLayer props={props} />
      {timeline.overlays.map((o, i) => (
        <Sequence key={i} from={f(o.start)} durationInFrames={Math.max(1, f(o.start + o.duration) - f(o.start))}
          name={`${o.type} ${i}`}>
          <OverlayView overlay={o} theme={props.theme} />
        </Sequence>
      ))}
      <AudioTracks props={props} />
    </AbsoluteFill>
  );
};
