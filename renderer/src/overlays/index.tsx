import {evolvePath} from '@remotion/paths';
import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {font} from '../fonts';
import type {Overlay, Theme} from '../types';
import {POSITION_Y, normWord, outline} from '../util';

type P<T extends Overlay['type']> = {o: Extract<Overlay, {type: T}>; theme: Theme};

const useAnim = (o: Overlay) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const total = Math.round(o.duration * fps);
  const enter = spring({frame, fps, config: {damping: 13, stiffness: 200, mass: 0.7}});
  const exit = interpolate(frame, [total - 6, total], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return {frame, fps, width, height, total, enter, exit, k: width / 1080};
};

const Highlighted: React.FC<{text: string; words: string[]; color: string}> = ({text, words, color}) => {
  const set = new Set(words.map(normWord));
  return (
    <>
      {text.split(/(\s+)/).map((w, i) => (
        <span key={i} style={set.has(normWord(w)) ? {color} : undefined}>{w}</span>
      ))}
    </>
  );
};

const KineticText: React.FC<P<'kineticText'>> = ({o, theme}) => {
  const {frame, fps, k, exit} = useAnim(o);
  const size = {m: 80, l: 112, xl: 150}[o.size] * k;
  const words = o.text.split(/\s+/);
  const hl = new Set(o.highlight.map(normWord));
  const color = o.color ?? theme.colors.text;
  const hcolor = o.highlightColor ?? theme.colors.highlight;
  const shown = o.animation === 'typewriter' ? Math.floor(frame / 1.5) : Infinity;
  let chars = 0;
  return (
    <AbsoluteFill style={{alignItems: 'center', opacity: exit}}>
      <div style={{position: 'absolute', top: `${POSITION_Y[o.position] * 100}%`, transform: 'translateY(-50%)', width: '90%',
        display: 'flex', flexWrap: 'wrap', justifyContent: 'center', flexDirection: o.animation === 'stack' ? 'column' : 'row',
        alignItems: 'center', columnGap: size * 0.25, fontFamily: font(theme.fonts.display), fontWeight: theme.fonts.displayWeight,
        fontSize: size, lineHeight: 1.02, textTransform: 'uppercase', textAlign: 'center'}}>
        {words.map((w, i) => {
          const s = spring({frame: frame - i * 3, fps, config: {damping: 11, stiffness: 240, mass: 0.6}});
          const visibleChars = Math.max(0, Math.min(w.length, shown - chars));
          chars += w.length + 1;
          const style: React.CSSProperties = {
            color: hl.has(normWord(w)) ? hcolor : color, textShadow: outline(7 * k, theme.colors.stroke), display: 'inline-block',
          };
          if (o.animation === 'pop' || o.animation === 'stack') {
            style.transform = `scale(${interpolate(s, [0, 1], [0.3, 1])})`;
            style.opacity = s > 0.01 ? 1 : 0;
          } else if (o.animation === 'slide') {
            style.transform = `translateX(${interpolate(s, [0, 1], [-200 * k, 0])}px)`;
            style.opacity = s;
          }
          return <span key={i} style={style}>{o.animation === 'typewriter' ? w.slice(0, visibleChars) : w}</span>;
        })}
      </div>
    </AbsoluteFill>
  );
};

const PriceStamp: React.FC<P<'priceStamp'>> = ({o, theme}) => {
  const {enter, exit, k, frame} = useAnim(o);
  const money = o.color ?? theme.colors.money;
  const top = `${POSITION_Y[o.position] * 100}%`;
  const scale = interpolate(enter, [0, 1], [0.4, 1]);
  if (o.variant === 'slime') {
    const wobble = Math.sin(frame / 3) * 2 * (1 - Math.min(1, frame / 20));
    return (
      <AbsoluteFill style={{alignItems: 'center', opacity: exit}}>
        <div style={{position: 'absolute', top, transform: `translateY(-50%) scale(${scale}) rotate(${-4 + wobble}deg)`, textAlign: 'center'}}>
          <div style={{fontFamily: font('Anton'), fontSize: 150 * k, lineHeight: 1, color: money, letterSpacing: '-0.01em',
            textShadow: `${outline(8 * k, '#0b3d0b')}, 0 ${14 * k}px 0 #0b3d0b`}}>{o.amount}</div>
          {o.label && <div style={{fontFamily: font('Anton'), fontSize: 64 * k, color: '#fff', textShadow: outline(6 * k)}}>{o.label}</div>}
        </div>
      </AbsoluteFill>
    );
  }
  if (o.variant === 'bubble') {
    return (
      <AbsoluteFill style={{alignItems: 'center', opacity: exit}}>
        <div style={{position: 'absolute', top, transform: `translateY(-50%) scale(${scale})`, background: '#fff', borderRadius: 40 * k,
          padding: `${18 * k}px ${44 * k}px`, boxShadow: '0 20px 60px rgba(0,0,0,0.35)', fontFamily: font(theme.fonts.display),
          fontWeight: 900, fontSize: 110 * k, color: money}}>{o.amount}</div>
      </AbsoluteFill>
    );
  }
  const badge = spring({frame: frame - 8, fps: 30, config: {damping: 10, stiffness: 260}});
  return (
    <AbsoluteFill style={{alignItems: 'center', opacity: exit}}>
      <div style={{position: 'absolute', top, transform: `translateY(-50%) scale(${scale})`, background: theme.colors.panel,
        borderRadius: 36 * k, padding: `${30 * k}px ${56 * k}px ${36 * k}px`, textAlign: 'center', minWidth: 520 * k,
        boxShadow: '0 24px 70px rgba(0,0,0,0.45)', fontFamily: font(theme.fonts.display)}}>
        {o.label && <div style={{fontWeight: 800, fontSize: 52 * k, color: theme.colors.panelText, textTransform: 'uppercase'}}>{o.label}</div>}
        <div style={{fontWeight: 900, fontSize: 150 * k, lineHeight: 1.05, color: money, textShadow: `0 ${4 * k}px 0 rgba(0,0,0,0.15)`}}>{o.amount}</div>
        {o.sublabel && (
          <div style={{display: 'inline-block', marginTop: 10 * k, background: money, color: '#fff', fontWeight: 900, fontSize: 54 * k,
            padding: `${8 * k}px ${40 * k}px`, borderRadius: 999, textTransform: 'uppercase', transform: `scale(${badge})`,
            boxShadow: `inset 0 -${6 * k}px 0 rgba(0,0,0,0.18)`}}>{o.sublabel}</div>
        )}
      </div>
    </AbsoluteFill>
  );
};

const LowerThird: React.FC<P<'lowerThird'>> = ({o, theme}) => {
  const {frame, fps, k, exit} = useAnim(o);
  const top = `${POSITION_Y[o.position] * 100}%`;
  if (o.variant === 'tag') {
    const s = spring({frame, fps, config: {damping: 14}});
    return (
      <AbsoluteFill style={{opacity: exit}}>
        <div style={{position: 'absolute', top, left: 60 * k, transform: `translateX(${interpolate(s, [0, 1], [-500 * k, 0])}px)`,
          background: theme.colors.tag, color: theme.colors.tagText, borderRadius: 14 * k, padding: `${12 * k}px ${26 * k}px`,
          fontFamily: font(theme.fonts.display), boxShadow: '0 10px 30px rgba(0,0,0,0.3)'}}>
          <div style={{fontWeight: 900, fontSize: 44 * k, textTransform: 'uppercase', lineHeight: 1.05}}>{o.title}</div>
          {o.subtitle && <div style={{fontWeight: 600, fontSize: 30 * k, opacity: 0.92}}>{o.subtitle}</div>}
        </div>
      </AbsoluteFill>
    );
  }
  const bar = (text: string, i: number, size: number, spacing: string) => {
    const s = spring({frame: frame - i * 4, fps, config: {damping: 16, stiffness: 180}});
    return (
      <div style={{background: theme.colors.lowerThird, color: theme.colors.lowerThirdText, fontFamily: font(theme.fonts.display),
        fontWeight: theme.fonts.displayWeight, fontSize: size * k, letterSpacing: spacing, textTransform: 'uppercase',
        padding: `${4 * k}px ${22 * k}px`, lineHeight: 1.15, transform: `scaleX(${s})`, transformOrigin: 'left center',
        border: `${3 * k}px solid ${theme.colors.lowerThirdText}`, whiteSpace: 'nowrap'}}>
        <span style={{opacity: interpolate(s, [0.5, 1], [0, 1], {extrapolateLeft: 'clamp'})}}>{text}</span>
      </div>
    );
  };
  return (
    <AbsoluteFill style={{alignItems: 'center', opacity: exit}}>
      <div style={{position: 'absolute', top, transform: 'translateY(-50%)', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 * k}}>
        {o.kicker && bar(o.kicker, 0, 34, '0.08em')}
        {bar(o.title, 1, 76, '0.18em')}
        {o.subtitle && bar(o.subtitle, 2, 30, '0.12em')}
      </div>
    </AbsoluteFill>
  );
};

const ListHeader: React.FC<P<'listHeader'>> = ({o, theme}) => {
  const {enter, exit, k, frame, fps} = useAnim(o);
  const sub = spring({frame: frame - 6, fps, config: {damping: 12}});
  return (
    <AbsoluteFill style={{alignItems: 'center', opacity: exit}}>
      <div style={{position: 'absolute', top: `${POSITION_Y[o.position] * 100}%`, textAlign: 'center', width: '90%',
        fontFamily: font(theme.fonts.display), color: theme.colors.text}}>
        <div style={{fontWeight: 900, fontSize: 104 * k, textShadow: outline(6 * k, theme.colors.stroke),
          transform: `scale(${interpolate(enter, [0, 1], [0.5, 1])})`}}>{o.number}. {o.title}</div>
        {o.subtitle && <div style={{fontWeight: 800, fontSize: 52 * k, marginTop: 4 * k, textShadow: outline(4 * k, theme.colors.stroke),
          opacity: sub, transform: `translateY(${(1 - sub) * 30 * k}px)`}}>{o.subtitle}</div>}
      </div>
    </AbsoluteFill>
  );
};

const ComingUp: React.FC<P<'comingUp'>> = ({o, theme}) => {
  const {enter, exit, k, frame} = useAnim(o);
  const dots = '...'.slice(0, (Math.floor(frame / 8) % 3) + 1);
  const text = o.text.replace(/\.+$/, '');
  return (
    <AbsoluteFill style={{opacity: exit}}>
      <div style={{position: 'absolute', top: 70 * k, left: 54 * k, transform: `translateX(${(1 - enter) * -400 * k}px)`,
        fontFamily: font(theme.fonts.display), fontWeight: 900, fontSize: 64 * k, color: theme.colors.highlight,
        textShadow: outline(5 * k, theme.colors.stroke)}}>{text}{dots}</div>
    </AbsoluteFill>
  );
};

const QuestionCard: React.FC<P<'questionCard'>> = ({o, theme}) => {
  const {enter, exit, k} = useAnim(o);
  return (
    <AbsoluteFill style={{backgroundColor: theme.colors.card, alignItems: 'center', justifyContent: 'center', opacity: Math.min(enter * 3, exit)}}>
      <div style={{width: '84%', textAlign: 'center', fontFamily: font(theme.fonts.display), transform: `scale(${interpolate(enter, [0, 1], [0.85, 1])})`}}>
        <div style={{fontWeight: 900, fontSize: 46 * k, color: theme.colors.highlight, letterSpacing: '0.04em', marginBottom: 20 * k,
          textShadow: '0 2px 0 rgba(0,0,0,0.15)'}}>{o.kicker}</div>
        <div style={{fontWeight: 900, fontSize: 84 * k, lineHeight: 1.12, color: theme.colors.cardText}}>
          <Highlighted text={o.text} words={o.highlight} color={theme.colors.accent} />
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Flash: React.FC<P<'flash'>> = ({o}) => {
  const {frame, total} = useAnim(o);
  const op = interpolate(frame, [0, total], [o.opacity, 0], {extrapolateRight: 'clamp'});
  return <AbsoluteFill style={{backgroundColor: o.color, opacity: op}} />;
};

const ArrowCallout: React.FC<P<"arrowCallout">> = ({o}) => {
  const {frame, fps, width, height, k, exit} = useAnim(o);
  const tipX = o.x * width;
  const tipY = o.y * height;
  const len = 300 * k;
  const a = (o.angle * Math.PI) / 180;
  const tailX = tipX + Math.cos(a) * len;
  const tailY = tipY + Math.sin(a) * len;
  const cx = (tipX + tailX) / 2 + Math.sin(a) * 90 * k;
  const cy = (tipY + tailY) / 2 - Math.cos(a) * 90 * k;
  const d = `M ${tailX} ${tailY} Q ${cx} ${cy} ${tipX} ${tipY}`;
  const p = interpolate(frame, [0, Math.round(fps * 0.35)], [0, 1], {extrapolateRight: 'clamp'});
  const ev = evolvePath(p, d);
  const ang = Math.atan2(tipY - cy, tipX - cx);
  const head = (s: number) => `M ${tipX} ${tipY} L ${tipX - Math.cos(ang + s) * 60 * k} ${tipY - Math.sin(ang + s) * 60 * k}`;
  const sw = 16 * k;
  return (
    <AbsoluteFill style={{opacity: exit}}>
      <svg width={width} height={height} style={{position: 'absolute'}}>
        <path d={d} stroke={o.color} strokeWidth={sw} fill="none" strokeLinecap="round" strokeDasharray={ev.strokeDasharray}
          strokeDashoffset={ev.strokeDashoffset} />
        {p >= 1 && [0.5, -0.5].map((s) => <path key={s} d={head(s)} stroke={o.color} strokeWidth={sw} strokeLinecap="round" />)}
      </svg>
      {o.text && (
        <div style={{position: 'absolute', left: tailX, top: tailY, transform: `translate(-50%, ${Math.sin(a) >= 0 ? '10%' : '-110%'}) rotate(-8deg)`,
          fontFamily: font('Anton'), fontSize: 96 * k, color: o.color, textShadow: outline(5 * k, '#fff'), whiteSpace: 'nowrap',
          opacity: interpolate(frame, [4, 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})}}>{o.text}</div>
      )}
    </AbsoluteFill>
  );
};

const InfoCard: React.FC<P<'infoCard'>> = ({o, theme}) => {
  const {enter, exit, k} = useAnim(o);
  const accent = o.accent ?? theme.colors.money;
  return (
    <AbsoluteFill style={{alignItems: 'center', opacity: exit}}>
      <div style={{position: 'absolute', top: `${POSITION_Y[o.position] * 100}%`, transform: `translateY(${(1 - enter) * -60 * k - 50}%)`,
        opacity: enter, width: '78%', background: theme.colors.infoCard, color: theme.colors.infoCardText, borderRadius: 28 * k,
        padding: `${26 * k}px ${34 * k}px`, fontFamily: font(theme.fonts.body), boxShadow: '0 20px 60px rgba(0,0,0,0.45)',
        border: '1px solid rgba(255,255,255,0.14)'}}>
        {o.title && <div style={{fontWeight: 800, fontSize: 40 * k, marginBottom: 12 * k}}>{o.title}</div>}
        {o.rows.map((r, i) => (
          <div key={i} style={{display: 'flex', justifyContent: 'space-between', fontSize: 38 * k, fontWeight: 600, padding: `${6 * k}px 0`,
            borderTop: i ? '1px solid rgba(255,255,255,0.1)' : 'none'}}>
            <span>{r.left}</span><span style={{color: accent, fontWeight: 800}}>{r.right}</span>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};

const PAPER = (color: string) => (
  <AbsoluteFill style={{backgroundColor: color}}>
    <svg width="100%" height="100%" style={{position: 'absolute', mixBlendMode: 'multiply', opacity: 0.5}}>
      <filter id="paper"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" seed="3" />
        <feColorMatrix values="0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0 0.5  0 0 0 0.7 0" /></filter>
      <rect width="100%" height="100%" filter="url(#paper)" />
    </svg>
  </AbsoluteFill>
);

const ImageInsert: React.FC<P<'imageInsert'>> = ({o, theme}) => {
  const {enter, exit, width, height, k} = useAnim(o);
  const file = o.media ?? o.src;
  const isVideo = /\.(mp4|mov|webm|m4v)$/i.test(file);
  const src = staticFile(file);
  const media = isVideo
    ? <OffthreadVideo src={src} muted style={{width: '100%', height: '100%', objectFit: 'cover'}} />
    : <Img src={src} style={{width: '100%', height: '100%', objectFit: 'cover'}} />;
  const w = width * o.scale;
  const h = o.frame === 'phone' ? w * 2.05 : o.frame === 'polaroid' ? w * 1.15 : w * (height / width);
  const frameStyle: React.CSSProperties =
    o.frame === 'phone'
      ? {border: `${18 * k}px solid #0d0d0f`, borderRadius: 70 * k, boxShadow: '0 30px 80px rgba(0,0,0,0.5)'}
      : o.frame === 'polaroid'
        ? {border: `${22 * k}px solid #fff`, borderBottomWidth: 90 * k, boxShadow: '0 30px 80px rgba(0,0,0,0.45)'}
        : {borderRadius: 24 * k, boxShadow: '0 30px 80px rgba(0,0,0,0.45)'};
  return (
    <AbsoluteFill style={{opacity: exit}}>
      {o.background === 'paper-red' && PAPER(theme.colors.paperRed)}
      {o.background === 'paper-blue' && PAPER(theme.colors.paperBlue)}
      {o.background === 'blur' && <AbsoluteFill style={{backdropFilter: 'blur(30px) brightness(0.7)'}} />}
      <div style={{position: 'absolute', left: o.x * width - w / 2, top: o.y * height - h / 2, width: w, height: h, overflow: 'hidden',
        transform: `scale(${interpolate(enter, [0, 1], [0.6, 1])}) rotate(${o.rotate * enter}deg)`, background: '#000', ...frameStyle}}>
        {media}
      </div>
    </AbsoluteFill>
  );
};

const Emoji: React.FC<P<'emoji'>> = ({o}) => {
  const {enter, exit, width, height, frame, k} = useAnim(o);
  return (
    <div style={{position: 'absolute', left: o.x * width, top: o.y * height, fontSize: o.size * k, opacity: exit,
      transform: `translate(-50%,-50%) scale(${enter}) rotate(${Math.sin(frame / 4) * 8}deg)`}}>{o.emoji}</div>
  );
};

const ProgressBar: React.FC<P<'progressBar'>> = ({o, theme}) => {
  const {frame, total, k} = useAnim(o);
  return (
    <AbsoluteFill>
      <div style={{position: 'absolute', top: 0, left: 0, height: 12 * k, width: `${(frame / total) * 100}%`,
        background: o.color ?? theme.colors.highlight}} />
    </AbsoluteFill>
  );
};

export const OverlayView: React.FC<{overlay: Overlay; theme: Theme}> = ({overlay, theme}) => {
  switch (overlay.type) {
    case 'kineticText': return <KineticText o={overlay} theme={theme} />;
    case 'priceStamp': return <PriceStamp o={overlay} theme={theme} />;
    case 'lowerThird': return <LowerThird o={overlay} theme={theme} />;
    case 'listHeader': return <ListHeader o={overlay} theme={theme} />;
    case 'comingUp': return <ComingUp o={overlay} theme={theme} />;
    case 'questionCard': return <QuestionCard o={overlay} theme={theme} />;
    case 'flash': return <Flash o={overlay} theme={theme} />;
    case 'arrowCallout': return <ArrowCallout o={overlay} theme={theme} />;
    case 'infoCard': return <InfoCard o={overlay} theme={theme} />;
    case 'imageInsert': return <ImageInsert o={overlay} theme={theme} />;
    case 'emoji': return <Emoji o={overlay} theme={theme} />;
    case 'progressBar': return <ProgressBar o={overlay} theme={theme} />;
  }
};
