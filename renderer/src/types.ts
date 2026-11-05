// Mirrors vh/timeline.py (the source of truth; see schemas/timeline.schema.json).
export type Position = 'top' | 'upper' | 'center' | 'lower' | 'bottom';

export type Transition = {
  type: 'cut' | 'whip' | 'flash' | 'zoom' | 'fade' | 'glitch' | 'slide';
  duration: number;
  direction: 'left' | 'right' | 'up' | 'down';
  color: string;
};

export type VideoClip = {
  id: string;
  source: string;
  kind: 'video' | 'image';
  start: number;
  duration: number;
  sourceIn: number;
  speed: number;
  volume: number;
  fit: 'cover' | 'contain' | 'blur';
  zoom?: {start: number; end: number; focusX: number; focusY: number};
  punchIns: number[];
  punchScale: number;
  transitionIn?: Transition;
  grade: 'none' | 'warm' | 'cool' | 'vivid' | 'bw' | 'film';
  src: string;
  srcIn?: number;
  tailMax?: number;
};

type Base = {start: number; duration: number; sfx?: string};
export type Overlay = Base &
  (
    | {type: 'kineticText'; text: string; highlight: string[]; position: Position; size: 'm' | 'l' | 'xl';
        animation: 'pop' | 'slide' | 'typewriter' | 'stack'; color?: string; highlightColor?: string}
    | {type: 'priceStamp'; amount: string; label?: string; sublabel?: string; variant: 'badge' | 'bubble' | 'slime';
        position: Position; color?: string}
    | {type: 'lowerThird'; title: string; kicker?: string; subtitle?: string; variant: 'stack' | 'tag'; position: Position}
    | {type: 'listHeader'; number: number | string; title: string; subtitle?: string; position: Position}
    | {type: 'comingUp'; text: string}
    | {type: 'questionCard'; text: string; kicker: string; highlight: string[]}
    | {type: 'flash'; color: string; opacity: number}
    | {type: 'arrowCallout'; text: string; x: number; y: number; angle: number; color: string}
    | {type: 'infoCard'; title?: string; rows: {left: string; right: string}[]; accent?: string; position: Position}
    | {type: 'imageInsert'; src: string; media?: string; mediaSrc?: string; frame: 'phone' | 'polaroid' | 'none';
        background: 'paper-red' | 'paper-blue' | 'blur' | 'none'; x: number; y: number; scale: number; rotate: number}
    | {type: 'emoji'; emoji: string; x: number; y: number; size: number}
    | {type: 'progressBar'; color?: string}
  );

export type Timeline = {
  version: 1;
  title: string;
  format: 'vertical' | 'horizontal' | 'square';
  fps: number;
  style: string;
  voiceover?: {src: string; start: number; volume: number};
  music?: {src: string; start: number; sourceIn: number; volume: number; duckTo: number; fadeIn: number; fadeOut: number};
  captions?: {src: string; preset?: CaptionPreset; position?: Position; maxWords?: number; uppercase?: boolean;
    highlight: string[]; hideDuring: [number, number][]};
  video: VideoClip[];
  overlays: Overlay[];
  sfx: {src: string; start: number; volume: number}[];
};

export type CaptionPreset = 'bold-pop' | 'karaoke' | 'subtle' | 'none';

export type Theme = {
  description?: string;
  fonts: {display: string; displayWeight: number; caption: string; captionWeight: number; body: string};
  colors: Record<
    'text' | 'stroke' | 'highlight' | 'accent' | 'money' | 'card' | 'cardText' | 'panel' | 'panelText' |
    'lowerThird' | 'lowerThirdText' | 'tag' | 'tagText' | 'infoCard' | 'infoCardText' | 'paperRed' | 'paperBlue',
    string
  >;
  captions: {preset: CaptionPreset; position: Position; maxWords: number; uppercase: boolean; size: number; strokeWidth: number};
  music?: {volume: number; duckTo: number};
};

export type Caption = {text: string; startMs: number; endMs: number; timestampMs: number | null; confidence: number | null};

export type Props = {
  timeline: Timeline;
  theme: Theme;
  captions: Caption[];
  speech: [number, number][];
  width: number;
  height: number;
  fps: number;
  durationInFrames: number;
};
