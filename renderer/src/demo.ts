import type {Props} from './types';

// Studio preview without media: shows every overlay type on a black background.
export const demoProps: Props = {
  width: 1080,
  height: 1920,
  fps: 30,
  durationInFrames: 30 * 12,
  captions: [],
  speech: [],
  theme: {
    fonts: {display: 'Montserrat', displayWeight: 900, caption: 'Montserrat', captionWeight: 900, body: 'Inter'},
    colors: {
      text: '#FFFFFF', stroke: '#000000', highlight: '#FFE135', accent: '#3DDC4A', money: '#2EE04F', card: '#FFFFFF',
      cardText: '#111111', panel: '#E9E9EC', panelText: '#555555', lowerThird: '#FFE135', lowerThirdText: '#111111',
      tag: '#1E6FFF', tagText: '#FFFFFF', infoCard: 'rgba(18,18,22,0.92)', infoCardText: '#FFFFFF', paperRed: '#D9433F',
      paperBlue: '#2D6CDF',
    },
    captions: {preset: 'bold-pop', position: 'center', maxWords: 3, uppercase: true, size: 92, strokeWidth: 7},
  },
  timeline: {
    version: 1, title: 'demo', format: 'vertical', fps: 30, style: 'raul', video: [], sfx: [],
    overlays: [
      {type: 'kineticText', start: 0, duration: 2, text: 'Y no pagué NADA', highlight: ['nada'], position: 'center', size: 'l', animation: 'pop'},
      {type: 'lowerThird', start: 2, duration: 2, kicker: 'Lugares secretos', title: 'Bangkok', subtitle: 'Raul Guillen', variant: 'stack', position: 'lower'},
      {type: 'priceStamp', start: 4, duration: 2, amount: '$8,833', label: 'First class', sublabel: 'Booked', variant: 'badge', position: 'center'},
      {type: 'questionCard', start: 6, duration: 2, kicker: 'PREGUNTA', text: '¿Se puede vivir con $500 al mes?', highlight: ['$500']},
      {type: 'listHeader', start: 8, duration: 2, number: 1, title: 'TDAC', subtitle: 'Gratis ✅', position: 'top'},
      {type: 'arrowCallout', start: 10, duration: 2, text: '1.9M', x: 0.5, y: 0.55, angle: -135, color: '#ff2a2a'},
    ],
  },
};
