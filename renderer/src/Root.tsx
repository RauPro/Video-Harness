import React from 'react';
import {Composition, type CalculateMetadataFunction} from 'remotion';
import {Main} from './Main';
import {demoProps} from './demo';
import type {Props} from './types';

const calculateMetadata: CalculateMetadataFunction<Props> = ({props}) => ({
  width: props.width,
  height: props.height,
  fps: props.fps,
  durationInFrames: props.durationInFrames,
});

export const Root: React.FC = () => (
  <Composition
    id="Main"
    component={Main}
    defaultProps={demoProps}
    calculateMetadata={calculateMetadata}
    width={1080}
    height={1920}
    fps={30}
    durationInFrames={demoProps.durationInFrames}
  />
);
