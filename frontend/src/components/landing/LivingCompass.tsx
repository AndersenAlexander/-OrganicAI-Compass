import { AudioWaveform, Leaf, MessageCircle, Mic, Network } from "lucide-react";
import {
  motion,
  useScroll,
  useSpring,
  useTransform,
  type MotionValue,
} from "motion/react";
import { useEffect, useId, useLayoutEffect, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import { useReducedMotionPreference } from "../../hooks/useReducedMotionPreference";

export type CompassVoiceState = "idle" | "connecting" | "listening" | "speaking" | "error";
export type LivingCompassSize = "logo" | "compact" | "guide" | "hero";

type CompassDialVariant = "logo" | "guide" | "stage";

type CompassDialProps = {
  voiceState: CompassVoiceState;
  variant?: CompassDialVariant;
};

type LivingCompassProps = {
  size?: LivingCompassSize;
  state?: CompassVoiceState;
  defaultState?: CompassVoiceState;
  onStateChange?: (state: CompassVoiceState) => void;
  onVoiceCoreClick?: () => void;
  voiceConnectionStatus?: string;
  interactive?: boolean;
  showPath?: boolean;
  showLabels?: boolean;
  showDebugControls?: boolean;
  className?: string;
  "aria-label"?: string;
};

type LivingCompassGuideLayerProps = {
  voiceState: CompassVoiceState;
  onVoiceStateChange?: (state: CompassVoiceState) => void;
  onVoiceCoreClick?: () => void;
  voiceConnectionStatus?: string;
  voiceAriaLabel?: string;
};

type LivingCompassHeroStageProps = {
  voiceState: CompassVoiceState;
  onVoiceStateChange: (state: CompassVoiceState) => void;
  onOpenCoach: (prompt?: string) => void;
};

type CompassAnchorName = "header" | "hero" | "footer";

type CompassAnchorPoint = {
  x: number;
  y: number;
  documentY: number;
  width: number;
};

type CompassJourneyLayout = {
  scrollStops: number[];
  xStops: number[];
  yStops: number[];
  scaleStops: number[];
  opacityStops: number[];
  headerRevealStop: number;
  heroArrivalStop: number;
  heroLockEnd: number;
  guideStart: number;
  footerDock: number;
  isMobile: boolean;
};

const compassTicks = Array.from({ length: 48 }, (_, index) => ({
  id: index,
  rotation: index * 7.5,
  major: index % 6 === 0,
}));

const voiceBars = Array.from({ length: 9 }, (_, index) => index);

const compassStages = ["Discover", "Understand", "Strategize", "Create", "Grow"];

const voiceStateLabels: Record<CompassVoiceState, string> = {
  idle: "Idle",
  connecting: "Connecting",
  listening: "Listening",
  speaking: "Speaking",
  error: "Voice unavailable",
};

const nextVoiceState: Record<CompassVoiceState, CompassVoiceState> = {
  idle: "connecting",
  connecting: "listening",
  listening: "speaking",
  speaking: "error",
  error: "idle",
};

const sizeToVariant: Record<LivingCompassSize, CompassDialVariant> = {
  logo: "logo",
  compact: "guide",
  guide: "guide",
  hero: "stage",
};

const COMPASS_BASE_SIZE = 320;

const fallbackJourneyLayout: CompassJourneyLayout = {
  scrollStops: [0, 6, 820, 1100, 2020, 4200, 4700, 5100, 5600],
  xStops: [82, 82, 960, 960, 720, 720, 720, 390, 82],
  yStops: [58, 58, 500, 500, 432, 432, 594, 650, 760],
  scaleStops: [0.15, 0.15, 1.42, 1.42, 0.725, 0.725, 0.595, 0.38, 0.14],
  opacityStops: [0, 1, 1, 1, 0.98, 0.98, 0.98, 1, 1],
  headerRevealStop: 6,
  heroArrivalStop: 820,
  heroLockEnd: 1100,
  guideStart: 2020,
  footerDock: 5600,
  isMobile: false,
};

function clampNumber(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function fallbackAnchor(name: CompassAnchorName, width: number, height: number): CompassAnchorPoint {
  const isMobile = width < 768;
  const isTablet = width >= 768 && width < 1200;
  if (name === "header") {
    const compactHeader = width < 1150;
    const narrowBrand = width <= 420;
    const headerGutter = compactHeader ? 12 : 22;
    const headerPadding = width <= 420 ? 12 : compactHeader ? 14 : 24;
    const headerHeight = compactHeader ? 68 : 82;
    const headerTop = compactHeader ? 10 : 18;
    const shellWidth = Math.min(1740, width - headerGutter * 2);
    const headerLeft = Math.max(headerGutter, (width - shellWidth) / 2);
    const anchorWidth = narrowBrand ? 40 : width < 640 ? 42 : 48;
    return {
      x: headerLeft + headerPadding + anchorWidth / 2 + 1,
      y: headerTop + headerHeight / 2,
      documentY: headerTop + headerHeight / 2,
      width: anchorWidth,
    };
  }
  if (name === "hero") {
    return {
      x: isMobile ? width / 2 : width * (isTablet ? 0.5 : 0.68),
      y: height * (isMobile ? 0.48 : 0.5),
      documentY: window.scrollY + height * (isMobile ? 0.48 : 0.5),
      width: isMobile ? 228 : isTablet ? 390 : 456,
    };
  }
  return {
    x: isMobile ? 34 : Math.max(64, (width - Math.min(1460, width - 64)) / 2 + 46),
    y: height - (isMobile ? 156 : 118),
    documentY: window.scrollY + height - (isMobile ? 156 : 118),
    width: isMobile ? 36 : 42,
  };
}

function measureAnchor(name: CompassAnchorName, width: number, height: number): CompassAnchorPoint {
  const fallback = fallbackAnchor(name, width, height);
  const element = document.querySelector<HTMLElement>(`[data-living-compass-anchor="${name}"]`);
  if (!element) return fallback;

  const rect = element.getBoundingClientRect();
  if (rect.width <= 0 || rect.height <= 0) return fallback;

  return {
    x: rect.left + rect.width / 2,
    y: rect.top + rect.height / 2,
    documentY: rect.top + window.scrollY + rect.height / 2,
    width: rect.width,
  };
}

function scaleFromAnchor(anchorWidth: number, fallbackScale: number) {
  const scale = anchorWidth / COMPASS_BASE_SIZE;
  if (!Number.isFinite(scale) || scale <= 0) return fallbackScale;
  return Math.min(1.55, Math.max(0.1, scale));
}

function pointAtScroll(anchor: CompassAnchorPoint, scrollPosition: number) {
  return {
    x: anchor.x,
    y: anchor.documentY - scrollPosition,
  };
}

function getCompassJourneyLayout(): CompassJourneyLayout {
  if (typeof window === "undefined") {
    return fallbackJourneyLayout;
  }

  const width = window.innerWidth || 1440;
  const height = window.innerHeight || 900;
  const isMobile = width < 768;
  const isTablet = width >= 768 && width < 1200;
  const documentHeight = Math.max(
    document.documentElement.scrollHeight,
    document.body.scrollHeight,
    height,
  );
  const maxScroll = Math.max(height, documentHeight - height);
  const headerAnchor = measureAnchor("header", width, height);
  const heroAnchor = measureAnchor("hero", width, height);
  const footerAnchor = measureAnchor("footer", width, height);
  const footerDock = maxScroll;
  const headerRevealStop = isMobile ? 4 : 6;
  const desktopHeroTravelRange = clampNumber(height * 0.78, 700, 1040);
  const minimumHeroViewportY = headerAnchor.y + Math.max(headerAnchor.width, heroAnchor.width * 0.26);
  const nonStickyHeroTravelRange = Math.max(
    headerRevealStop + 1,
    Math.min(
      clampNumber(height * (isMobile ? 0.58 : 0.72), isMobile ? 420 : 700, isMobile ? 700 : 1040),
      heroAnchor.documentY - minimumHeroViewportY,
    ),
  );
  const heroArrivalStop = isMobile || isTablet ? nonStickyHeroTravelRange : desktopHeroTravelRange;
  const heroHoldRange = clampNumber(height * (isMobile ? 0.2 : 0.27), isMobile ? 150 : 220, isMobile ? 260 : 360);
  const heroToGuideRange = clampNumber(height * (isMobile ? 0.68 : isTablet ? 0.76 : 0.86), isMobile ? 520 : 720, isMobile ? 820 : 1040);
  const heroLockEnd = heroArrivalStop + heroHoldRange;
  const guideStart = heroLockEnd + heroToGuideRange;
  const footerRange = clampNumber(height * (isMobile ? 0.82 : 1.16), isMobile ? 560 : 820, isMobile ? 920 : 1300);
  const footerStart = Math.max(guideStart + 1, footerDock - footerRange);
  const footerDown = footerStart + footerRange * 0.48;
  const footerCurve = footerStart + footerRange * 0.76;
  const scrollStops = enforceIncreasingStops([
    0,
    headerRevealStop,
    heroArrivalStop,
    heroLockEnd,
    guideStart,
    footerStart,
    footerDown,
    footerCurve,
    footerDock,
  ]);

  const headerPoint = {
    x: headerAnchor.x,
    y: headerAnchor.y,
  };
  const measuredHeroLockPoint = isMobile || isTablet
    ? pointAtScroll(heroAnchor, heroArrivalStop)
    : {
        x: heroAnchor.x,
        y: heroAnchor.y,
      };
  const heroLockPoint = {
    x: measuredHeroLockPoint.x,
    y: Math.max(headerPoint.y + 1, measuredHeroLockPoint.y),
  };
  const guidePoint = {
    x: width / 2,
    y: height * (isMobile ? 0.5 : 0.48),
  };
  const footerDockPoint = pointAtScroll(footerAnchor, scrollStops[8]);
  const footerDownPoint = {
    x: guidePoint.x,
    y: isMobile ? guidePoint.y : Math.min(height - 136, guidePoint.y + height * 0.18),
  };
  const footerCurvePoint = {
    x: guidePoint.x + (footerDockPoint.x - guidePoint.x) * (isMobile ? 0.64 : 0.56),
    y: footerDownPoint.y + (footerDockPoint.y - footerDownPoint.y) * (isMobile ? 0.56 : 0.42),
  };
  const logoScale = scaleFromAnchor(headerAnchor.width, isMobile ? 0.13 : 0.15);
  const heroScale = scaleFromAnchor(heroAnchor.width, isMobile ? 0.72 : isTablet ? 1.22 : 1.42);
  const guideScale = isMobile ? 0.35 : isTablet ? 0.6 : 0.725;
  const footerScale = scaleFromAnchor(footerAnchor.width, isMobile ? 0.12 : 0.135);
  const footerMidScale = isMobile ? Math.max(footerScale * 1.85, guideScale * 0.82) : 190 / COMPASS_BASE_SIZE;
  const footerCurveScale = footerMidScale + (footerScale - footerMidScale) * 0.45;

  return {
    scrollStops,
    xStops: [headerPoint.x, headerPoint.x, heroLockPoint.x, heroLockPoint.x, guidePoint.x, guidePoint.x, footerDownPoint.x, footerCurvePoint.x, footerDockPoint.x],
    yStops: [headerPoint.y, headerPoint.y, heroLockPoint.y, heroLockPoint.y, guidePoint.y, guidePoint.y, footerDownPoint.y, footerCurvePoint.y, footerDockPoint.y],
    scaleStops: [logoScale, logoScale, heroScale, heroScale, guideScale, guideScale, footerMidScale, footerCurveScale, footerScale],
    opacityStops: [0, 1, 1, 1, 0.98, 0.98, 0.98, 1, 1],
    headerRevealStop,
    heroArrivalStop,
    heroLockEnd,
    guideStart,
    footerDock,
    isMobile,
  };
}

function measureDocumentY(selector: string, fallback: number) {
  const element = document.querySelector(selector);
  if (!element) return fallback;
  return element.getBoundingClientRect().top + window.scrollY;
}

function measureDocumentHeight(selector: string, fallback: number) {
  const element = document.querySelector(selector);
  if (!element) return fallback;
  return element.getBoundingClientRect().height || fallback;
}

function enforceIncreasingStops(stops: number[]) {
  return stops.reduce<number[]>((accumulator, stop) => {
    const previous = accumulator[accumulator.length - 1] ?? -1;
    accumulator.push(Math.max(stop, previous + 1));
    return accumulator;
  }, []);
}

function useCompassJourneyLayout() {
  const [layout, setLayout] = useState<CompassJourneyLayout>(() => getCompassJourneyLayout());

  useEffect(() => {
    let timeout: number | undefined;
    let resizeObserver: ResizeObserver | undefined;
    let delayedUpdates: number[] = [];

    const update = () => setLayout(getCompassJourneyLayout());
    const scheduleUpdate = () => {
      window.clearTimeout(timeout);
      timeout = window.setTimeout(update, 120);
    };

    update();
    window.addEventListener("resize", scheduleUpdate);
    window.addEventListener("orientationchange", scheduleUpdate);
    window.addEventListener("load", scheduleUpdate);
    void document.fonts?.ready.then(scheduleUpdate).catch(() => undefined);
    if ("ResizeObserver" in window) {
      resizeObserver = new ResizeObserver(scheduleUpdate);
      resizeObserver.observe(document.body);
      document.querySelectorAll<HTMLElement>("[data-living-compass-anchor]").forEach((element) => {
        resizeObserver?.observe(element);
      });
    }
    delayedUpdates = [300, 900, 1800, 3000].map((delay) => window.setTimeout(update, delay));

    return () => {
      window.clearTimeout(timeout);
      delayedUpdates.forEach((delayedUpdate) => window.clearTimeout(delayedUpdate));
      resizeObserver?.disconnect();
      window.removeEventListener("resize", scheduleUpdate);
      window.removeEventListener("orientationchange", scheduleUpdate);
      window.removeEventListener("load", scheduleUpdate);
    };
  }, []);

  useLayoutEffect(() => {
    setLayout(getCompassJourneyLayout());
  }, []);

  return layout;
}

function VoiceCore({ state }: { state: CompassVoiceState }) {
  return (
    <div className={`living-voice-core living-voice-core--${state}`} aria-hidden="true">
      <span className="living-voice-core__halo" />
      <span className="living-voice-core__orb" />
      <span className="living-voice-core__ripple living-voice-core__ripple--one" />
      <span className="living-voice-core__ripple living-voice-core__ripple--two" />
      <span className="living-voice-core__waveform">
        {voiceBars.map((bar) => (
          <i key={bar} style={{ "--bar-index": bar } as CSSProperties} />
        ))}
      </span>
    </div>
  );
}

function CompassOrganicFrame() {
  return (
    <g className="living-compass__organic-frame" aria-hidden="true">
      <path d="M38 72 C22 87 19 116 37 139 C48 154 65 158 80 151" />
      <path d="M182 69 C203 82 207 116 185 143 C174 157 158 162 142 154" />
      <path d="M78 36 C93 14 128 11 148 31 C158 41 163 56 159 72" />
      <path d="M74 184 C94 207 131 207 151 184 C160 174 163 160 159 147" />
      <circle cx="36" cy="139" r="2.8" />
      <circle cx="184" cy="143" r="2.8" />
      <circle cx="148" cy="31" r="2.8" />
      <circle cx="74" cy="184" r="2.8" />
    </g>
  );
}

function CompassPathOrigin() {
  return (
    <svg className="living-compass-path-origin" viewBox="0 0 220 118" preserveAspectRatio="none" aria-hidden="true">
      <path className="living-compass-path-origin__glow" d="M110 2 C116 31 89 44 101 70 C108 87 132 91 139 116" />
      <path className="living-compass-path-origin__line" d="M110 2 C116 31 89 44 101 70 C108 87 132 91 139 116" />
    </svg>
  );
}

export function CompassDial({ voiceState, variant = "guide" }: CompassDialProps) {
  const gradientId = useId().replace(/:/g, "");
  const coreGlowId = `livingCompassCoreGlow-${gradientId}`;
  const needleId = `livingCompassNeedle-${gradientId}`;
  const softGlowId = `livingCompassSoftGlow-${gradientId}`;

  return (
    <div className={`living-compass living-compass--${variant} living-compass--${voiceState}`}>
      <svg className="living-compass__dial" viewBox="0 0 220 220" aria-hidden="true">
        <defs>
          <radialGradient id={coreGlowId} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--voice-core-highlight)" stopOpacity="0.95" />
            <stop offset="42%" stopColor="var(--voice-core-mid)" stopOpacity="0.72" />
            <stop offset="100%" stopColor="var(--voice-core-tail)" stopOpacity="0" />
          </radialGradient>
          <linearGradient id={needleId} x1="68" x2="152" y1="44" y2="176">
            <stop offset="0%" stopColor="#d9fff9" />
            <stop offset="50%" stopColor="#42e8d0" />
            <stop offset="100%" stopColor="#8cdd42" />
          </linearGradient>
          <filter id={softGlowId} x="-35%" y="-35%" width="170%" height="170%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        <circle className="living-compass__aura" cx="110" cy="110" r="96" style={{ fill: `url(#${coreGlowId})` }} />
        <CompassOrganicFrame />
        <circle className="living-compass__ring living-compass__ring--outer" cx="110" cy="110" r="92" />
        <circle className="living-compass__ring living-compass__ring--middle" cx="110" cy="110" r="72" />
        <circle className="living-compass__ring living-compass__ring--inner" cx="110" cy="110" r="43" />
        <ellipse className="living-compass__orbit living-compass__orbit--one" cx="110" cy="110" rx="89" ry="34" />
        <ellipse className="living-compass__orbit living-compass__orbit--two" cx="110" cy="110" rx="78" ry="29" />

        <g className="living-compass__ticks">
          {compassTicks.map((tick) => (
            <line
              key={tick.id}
              x1="110"
              x2="110"
              y1="17"
              y2={tick.major ? 30 : 24}
              className={tick.major ? "living-compass__tick living-compass__tick--major" : "living-compass__tick"}
              transform={`rotate(${tick.rotation} 110 110)`}
            />
          ))}
        </g>

        <g className="living-compass__markers">
          <text x="110" y="35" textAnchor="middle">
            N
          </text>
          <text x="185" y="115" textAnchor="middle">
            E
          </text>
          <text x="110" y="194" textAnchor="middle">
            S
          </text>
          <text x="35" y="115" textAnchor="middle">
            W
          </text>
        </g>

        <g className="living-compass__direction-points">
          <path d="M110 19 L116 46 L110 39 L104 46 Z" />
          <path d="M201 110 L174 116 L181 110 L174 104 Z" />
          <path d="M110 201 L104 174 L110 181 L116 174 Z" />
          <path d="M19 110 L46 104 L39 110 L46 116 Z" />
        </g>
        <path
          className="living-compass__needle-shadow"
          d="M110 38 L121 110 L110 182 L99 110 Z"
          style={{ filter: `url(#${softGlowId})` }}
        />
        <path className="living-compass__needle" d="M110 38 L121 110 L110 182 L99 110 Z" style={{ fill: `url(#${needleId})` }} />
        <circle className="living-compass__center-well" cx="110" cy="110" r="36" />
        <circle className="living-compass__core-glow" cx="110" cy="110" r="44" style={{ fill: `url(#${coreGlowId})` }} />
      </svg>
      <VoiceCore state={voiceState} />
      <span className="living-compass__hover-ring" aria-hidden="true" />
    </div>
  );
}

function renderCompassSurface({
  activeState,
  variant,
  interactive,
  reducedMotion,
  onCycle,
  onPress,
  voiceConnectionStatus,
  ariaLabel,
}: {
  activeState: CompassVoiceState;
  variant: CompassDialVariant;
  interactive: boolean;
  reducedMotion: boolean;
  onCycle: () => void;
  onPress?: () => void;
  voiceConnectionStatus?: string;
  ariaLabel: string;
}) {
  const content = <CompassDial voiceState={activeState} variant={variant} />;

  if (!interactive) {
    return <div className="living-compass-component__surface">{content}</div>;
  }

  return (
    <motion.button
      type="button"
      className="living-compass-component__surface living-compass-component__surface--button"
      data-voice-connection-status={voiceConnectionStatus}
      aria-label={ariaLabel}
      whileHover={reducedMotion ? undefined : { scale: 1.035 }}
      whileTap={reducedMotion ? undefined : { scale: 0.99 }}
      onClick={onPress ?? onCycle}
    >
      {content}
    </motion.button>
  );
}

export function LivingCompass({
  size = "hero",
  state,
  defaultState = "idle",
  onStateChange,
  onVoiceCoreClick,
  voiceConnectionStatus,
  interactive = false,
  showPath = true,
  showLabels = true,
  showDebugControls = false,
  className = "",
  "aria-label": ariaLabel,
}: LivingCompassProps) {
  const [internalState, setInternalState] = useState<CompassVoiceState>(defaultState);
  const reducedMotion = useReducedMotionPreference();
  const activeState = state ?? internalState;
  const variant = sizeToVariant[size];

  const setState = (nextState: CompassVoiceState) => {
    if (state === undefined) setInternalState(nextState);
    onStateChange?.(nextState);
  };
  const cycleState = () => setState(nextVoiceState[activeState]);
  const rootClassName = [
    "living-compass-component",
    `living-compass-component--${size}`,
    `living-compass-component--${activeState}`,
    showPath ? "living-compass-component--with-path" : "",
    showLabels ? "living-compass-component--with-labels" : "",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  const surface = size === "logo" ? (
    <div className="living-compass-component__surface">
      <CompassDial voiceState={activeState} variant={variant} />
    </div>
  ) : (
    renderCompassSurface({
      activeState,
      variant,
      interactive,
      reducedMotion,
      onCycle: cycleState,
      onPress: onVoiceCoreClick,
      voiceConnectionStatus,
      ariaLabel: ariaLabel ?? `Living Compass voice core, ${voiceStateLabels[activeState]} state. Click to cycle state.`,
    })
  );

  return (
    <div className={rootClassName} data-state={activeState} data-voice-connection-status={voiceConnectionStatus}>
      <div className="living-compass-component__stage">
        {surface}
        {showLabels && size !== "logo" ? (
          <div className="living-compass-component__labels" aria-hidden="true">
            {compassStages.map((stage, index) => (
              <span key={stage} className={`living-compass-component__label living-compass-component__label--${index + 1}`}>
                {stage}
              </span>
            ))}
          </div>
        ) : null}
        {showPath && size !== "logo" ? <CompassPathOrigin /> : null}
      </div>
      {showDebugControls ? <VoiceStateControls value={activeState} onChange={setState} mode="inline" /> : null}
    </div>
  );
}

export function LivingCompassLogoMark() {
  return (
    <span className="living-compass-logo-mark" aria-hidden="true">
      <LivingCompass size="logo" state="idle" showPath={false} showLabels={false} />
      <Leaf size={13} className="living-compass-logo-mark__satellite living-compass-logo-mark__satellite--leaf" />
      <Network size={12} className="living-compass-logo-mark__satellite living-compass-logo-mark__satellite--network" />
    </span>
  );
}

function CompassPath({
  progress,
  disabled,
}: {
  progress: MotionValue<number>;
  disabled: boolean;
}) {
  const pathLength = useTransform(progress, [0.02, 0.94], [0, 1]);
  const opacity = useTransform(progress, [0, 0.05, 0.88, 1], [0, 0.66, 0.48, 0.12]);

  if (disabled) return null;

  return (
    <motion.svg
      className="living-compass-path"
      viewBox="0 0 1000 1600"
      preserveAspectRatio="none"
      aria-hidden="true"
      style={{ opacity }}
    >
      <path
        className="living-compass-path__soft"
        d="M500 24 L500 1576"
      />
      <motion.path
        className="living-compass-path__active"
        d="M500 24 L500 1576"
        style={{ pathLength }}
      />
      <motion.path
        className="living-compass-path__spark"
        d="M500 24 L500 1576"
        style={{ pathLength }}
      />
    </motion.svg>
  );
}

function VoiceStateControls({
  value,
  onChange,
  mode = "fixed",
}: {
  value: CompassVoiceState;
  onChange: (state: CompassVoiceState) => void;
  mode?: "fixed" | "inline";
}) {
  return (
    <div className={`living-compass-dev-panel living-compass-dev-panel--${mode}`} aria-label="Voice core state control">
      {(Object.keys(voiceStateLabels) as CompassVoiceState[]).map((state) => (
        <button
          key={state}
          type="button"
          className={state === value ? "is-active" : ""}
          aria-pressed={state === value}
          onClick={() => onChange(state)}
        >
          {voiceStateLabels[state]}
        </button>
      ))}
    </div>
  );
}

export function LivingCompassGuideLayer({
  voiceState,
  onVoiceStateChange,
  onVoiceCoreClick,
  voiceConnectionStatus,
  voiceAriaLabel,
}: LivingCompassGuideLayerProps) {
  const { scrollY, scrollYProgress } = useScroll();
  const layout = useCompassJourneyLayout();
  const reducedMotion = useReducedMotionPreference();
  const [portalTarget, setPortalTarget] = useState<HTMLElement | null>(null);
  const [guideReleased, setGuideReleased] = useState(false);

  useEffect(() => {
    setPortalTarget(document.body);
    return () => setPortalTarget(null);
  }, []);

  useEffect(() => {
    const updateGuideRelease = (value: number) => {
      const nextReleased = value >= layout.headerRevealStop;
      setGuideReleased((current) => (current === nextReleased ? current : nextReleased));
    };

    updateGuideRelease(scrollY.get());
    return scrollY.on("change", updateGuideRelease);
  }, [layout.headerRevealStop, scrollY]);

  const xRaw = useTransform(scrollY, layout.scrollStops, layout.xStops);
  const yRaw = useTransform(scrollY, layout.scrollStops, layout.yStops);
  const scaleRaw = useTransform(scrollY, layout.scrollStops, layout.scaleStops);
  const opacityRaw = useTransform(scrollY, layout.scrollStops, layout.opacityStops);
  const previewScrollStops = [
    layout.scrollStops[0],
    layout.scrollStops[1],
    layout.headerRevealStop + (layout.heroArrivalStop - layout.headerRevealStop) * 0.28,
    layout.headerRevealStop + (layout.heroArrivalStop - layout.headerRevealStop) * 0.52,
    layout.headerRevealStop + (layout.heroArrivalStop - layout.headerRevealStop) * 0.72,
    layout.heroArrivalStop,
  ];
  const previewOpacityRaw = useTransform(scrollY, previewScrollStops, [1, 1, 0.5, 0.1, 0, 0]);
  const springConfig = { stiffness: 140, damping: 34, mass: 0.55 };
  const xSmooth = useSpring(xRaw, springConfig);
  const ySmooth = useSpring(yRaw, springConfig);
  const scaleSmooth = useSpring(scaleRaw, springConfig);
  const opacitySmooth = useSpring(opacityRaw, { stiffness: 150, damping: 34, mass: 0.5 });

  useEffect(() => {
    const root = document.documentElement;
    const updatePreviewOpacity = (value: number) => {
      root.style.setProperty("--living-compass-hero-preview-opacity", value.toFixed(3));
    };

    updatePreviewOpacity(previewOpacityRaw.get());
    const unsubscribe = previewOpacityRaw.on("change", updatePreviewOpacity);
    return () => {
      unsubscribe();
      root.style.removeProperty("--living-compass-hero-preview-opacity");
    };
  }, [previewOpacityRaw]);

  const travelerStyle = {
    x: reducedMotion ? xRaw : xSmooth,
    y: reducedMotion ? yRaw : ySmooth,
    scale: reducedMotion ? scaleRaw : scaleSmooth,
    opacity: reducedMotion ? opacityRaw : opacitySmooth,
  };

  const layer = (
    <div className="living-compass-guide-layer" data-reduced-motion={reducedMotion ? "true" : "false"}>
      <CompassPath progress={scrollYProgress} disabled={reducedMotion} />
      <motion.div
        className="living-compass-traveler"
        data-living-compass-traveler="true"
        data-released={guideReleased ? "true" : "false"}
        style={travelerStyle}
      >
        <div className="living-compass-traveler__center">
          <LivingCompass
            size="guide"
            state={voiceState}
            interactive={guideReleased}
            showPath={false}
            showLabels={false}
            onStateChange={onVoiceStateChange}
            onVoiceCoreClick={onVoiceCoreClick}
            voiceConnectionStatus={voiceConnectionStatus}
            aria-label={voiceAriaLabel}
          />
        </div>
      </motion.div>
    </div>
  );

  return portalTarget ? createPortal(layer, portalTarget) : null;
}

export function LivingCompassHeroStage({ voiceState, onVoiceStateChange, onOpenCoach }: LivingCompassHeroStageProps) {
  return (
    <section
      id="living-compass"
      className="home-living-compass home-conversion-section"
      data-compass-anchor="center"
      data-testid="home-living-compass"
    >
      <div className="home-living-compass__atmosphere" aria-hidden="true" />
      <div className="home-living-compass__copy">
        <p className="home-eyebrow">LIVING COMPASS</p>
        <h2>The logo becomes the guide.</h2>
        <p>
          OrganicAI Compass turns the compass symbol into a calm voice-guided narrator: it starts in the header, opens
          into the central AI core, then travels with the page as each decision layer appears.
        </p>
        <div className="home-living-compass__actions">
          <button type="button" className="home-button" onClick={() => onVoiceStateChange("listening")}>
            <Mic size={16} /> Preview Listening
          </button>
          <button type="button" onClick={() => onVoiceStateChange("speaking")}>
            <AudioWaveform size={16} /> Preview Speaking
          </button>
          <button
            type="button"
            onClick={() => onOpenCoach("Help me understand how OrganicAI Compass can guide my next career decision.")}
          >
            <MessageCircle size={16} /> Open Coach
          </button>
        </div>
      </div>

      <div className="home-living-compass__stage" aria-hidden="true">
        <div className="home-living-compass__anchor" data-living-compass-anchor="hero">
          <span />
          <span />
          <span />
        </div>
        <div className="home-living-compass__dock">
          <span />
          <span />
          <span />
        </div>
        {compassStages.map((stage, index) => (
          <span key={stage} className={`home-living-compass__label home-living-compass__label--${index + 1}`}>
            {stage}
          </span>
        ))}
      </div>
    </section>
  );
}
