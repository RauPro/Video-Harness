import {loadFont as anton} from '@remotion/google-fonts/Anton';
import {loadFont as bebas} from '@remotion/google-fonts/BebasNeue';
import {loadFont as inter} from '@remotion/google-fonts/Inter';
import {loadFont as montserrat} from '@remotion/google-fonts/Montserrat';

const opts = {subsets: ['latin', 'latin-ext'] as ('latin' | 'latin-ext')[]};
const loaders: Record<string, () => {fontFamily: string}> = {
  Montserrat: () => montserrat('normal', {...opts, weights: ['600', '700', '800', '900']}),
  Inter: () => inter('normal', {...opts, weights: ['400', '600', '700', '800']}),
  Anton: () => anton('normal', {...opts, weights: ['400']}),
  BebasNeue: () => bebas('normal', {...opts, weights: ['400']}),
};
const loaded: Record<string, string> = {};

/** CSS font-family for a theme font name; unknown names fall back to a system stack. */
export const font = (name: string): string => {
  if (!loaded[name]) {
    const load = loaders[name];
    loaded[name] = load ? `'${load().fontFamily}', sans-serif` : `${name}, 'Helvetica Neue', Arial, sans-serif`;
  }
  return loaded[name];
};
