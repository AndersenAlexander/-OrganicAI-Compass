import { ArrowRight, ChevronLeft, ChevronRight, Pause, Play } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type CSSProperties } from "react";
import { Link } from "react-router-dom";
import {
  heroVideoFallbackDurationMs,
  type HeroVideoSlide,
  type HeroVideoAction,
} from "../../config/heroVideoSlides";

type HeroContentMode = "welcome" | "actions-only";

type HeroVideoSliderProps = {
  slides: HeroVideoSlide[];
  contentMode?: HeroContentMode;
  welcomeTitle?: string;
  showPlayControl?: boolean;
  primaryAction?: HeroVideoAction;
  secondaryAction?: HeroVideoAction;
};

type NavigatorWithConnection = Navigator & {
  connection?: {
    saveData?: boolean;
  };
};

function usePrefersReducedMotion() {
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);

  useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setPrefersReducedMotion(media.matches);

    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  return prefersReducedMotion;
}

function useSaveDataPreference() {
  const [saveData, setSaveData] = useState(false);

  useEffect(() => {
    setSaveData(Boolean((navigator as NavigatorWithConnection).connection?.saveData));
  }, []);

  return saveData;
}

const defaultPrimaryAction: HeroVideoAction = { label: "Start Your Diagnostic", to: "/diagnostic" };
const defaultSecondaryAction: HeroVideoAction = { label: "See How It Works", to: "/how-it-works" };

export function HeroVideoSlider({
  slides,
  contentMode = "welcome",
  welcomeTitle = "Welcome to OrganicAI Compass",
  showPlayControl = true,
  primaryAction = defaultPrimaryAction,
  secondaryAction = defaultSecondaryAction,
}: HeroVideoSliderProps) {
  const prefersReducedMotion = usePrefersReducedMotion();
  const saveData = useSaveDataPreference();
  const videoRefs = useRef<Record<string, HTMLVideoElement | null>>({});
  const paginationRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const paginationContainerRef = useRef<HTMLDivElement | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [failedVideos, setFailedVideos] = useState<Set<string>>(() => new Set());
  const activeSlide = slides[activeIndex] ?? slides[0];
  const hasMultipleSlides = slides.length > 1;

  useEffect(() => {
    if (prefersReducedMotion || saveData) setIsPaused(true);
  }, [prefersReducedMotion, saveData]);

  const markVideoFailed = useCallback((slideId: string) => {
    setFailedVideos((current) => {
      if (current.has(slideId)) return current;
      const next = new Set(current);
      next.add(slideId);
      return next;
    });
  }, []);

  const goToSlide = useCallback(
    (nextIndex: number) => {
      if (!slides.length) return;
      setActiveIndex((nextIndex + slides.length) % slides.length);
    },
    [slides.length],
  );

  const goToNext = useCallback(() => goToSlide(activeIndex + 1), [activeIndex, goToSlide]);
  const goToPrevious = useCallback(() => goToSlide(activeIndex - 1), [activeIndex, goToSlide]);

  useEffect(() => {
    slides.forEach((slide, index) => {
      const video = videoRefs.current[slide.id];
      if (!video) return;

      const shouldPlay =
        index === activeIndex &&
        !isPaused &&
        !prefersReducedMotion &&
        !saveData &&
        !failedVideos.has(slide.id);

      video.muted = true;

      if (!shouldPlay) {
        video.pause();
        if (index !== activeIndex) {
          try {
            video.currentTime = 0;
          } catch {
            // Some browsers disallow resetting media before metadata is available.
          }
        }
        return;
      }

      const playAttempt = video.play();
      if (playAttempt) {
        playAttempt.catch(() => markVideoFailed(slide.id));
      }
    });
  }, [activeIndex, failedVideos, isPaused, markVideoFailed, prefersReducedMotion, saveData, slides]);

  useEffect(() => {
    if (!activeSlide || !hasMultipleSlides || isPaused || prefersReducedMotion) return;

    const useTimer =
      Boolean(activeSlide.advanceAfterMs) || saveData || failedVideos.has(activeSlide.id) || activeSlide.sources.length === 0;
    if (!useTimer) return;

    const timeout = window.setTimeout(
      goToNext,
      activeSlide.advanceAfterMs ?? activeSlide.fallbackDurationMs ?? heroVideoFallbackDurationMs,
    );
    return () => window.clearTimeout(timeout);
  }, [activeSlide, failedVideos, goToNext, hasMultipleSlides, isPaused, prefersReducedMotion, saveData]);

  useEffect(() => {
    if (!activeSlide) return;
    const pagination = paginationContainerRef.current;
    const activeButton = paginationRefs.current[activeSlide.id];
    if (!pagination || !activeButton) return;

    const centeredScrollLeft =
      activeButton.offsetLeft - (pagination.clientWidth - activeButton.offsetWidth) / 2;
    pagination.scrollLeft = Math.max(0, centeredScrollLeft);
  }, [activeSlide]);

  if (!activeSlide) return null;

  const shouldRenderSources = (slide: HeroVideoSlide) =>
    !prefersReducedMotion && !saveData && !failedVideos.has(slide.id) && slide.sources.length > 0;

  return (
    <section className="home-video-hero" aria-labelledby="home-title" data-testid="home-video-hero">
      <div className="home-video-hero__stage" aria-hidden="true">
        {slides.map((slide, index) => {
          const isActive = index === activeIndex;
          return (
            <div
              key={slide.id}
              className={isActive ? "home-video-hero__slide is-active" : "home-video-hero__slide"}
              data-testid={`hero-slide-${slide.id}`}
              data-active={isActive ? "true" : "false"}
              style={{ "--hero-object-position": slide.objectPosition ?? "center center" } as CSSProperties}
            >
              <img
                className="home-video-hero__poster"
                src={slide.posterSrc}
                alt=""
                loading={index === 0 ? "eager" : "lazy"}
                decoding="async"
              />
              <video
                ref={(node) => {
                  videoRefs.current[slide.id] = node;
                }}
                className="home-video-hero__video"
                muted
                playsInline
                preload={isActive ? "metadata" : "none"}
                poster={slide.posterSrc}
                loop={slide.loop}
                data-testid={`hero-video-${slide.id}`}
                onEnded={() => {
                  if (isActive && !isPaused && !prefersReducedMotion) goToNext();
                }}
                onError={() => markVideoFailed(slide.id)}
                onStalled={() => markVideoFailed(slide.id)}
              >
                {shouldRenderSources(slide)
                  ? slide.sources.map((source) => <source key={source.src} src={source.src} type={source.type} />)
                  : null}
              </video>
            </div>
          );
        })}
      </div>

      <div className="home-video-hero__overlay" aria-hidden="true" />

      <div className="home-video-hero__content">
        <div className="home-video-hero__copy" data-testid="hero-copy">
          {contentMode === "welcome" ? (
            <h1 id="home-title">{welcomeTitle}</h1>
          ) : (
            <h1 id="home-title" className="home-video-hero__sr-title">
              {welcomeTitle}
            </h1>
          )}

          <div className="home-hero-actions">
            <Link className="home-button" to={primaryAction.to}>
              {primaryAction.label} <ArrowRight size={17} />
            </Link>
            {secondaryAction ? (
              <Link className="home-button secondary" to={secondaryAction.to}>
                {secondaryAction.label}
              </Link>
            ) : null}
            {showPlayControl ? (
              <button
                type="button"
                className="home-video-hero__play"
                onClick={() => setIsPaused((current) => !current)}
                aria-label={isPaused ? "Play background video" : "Pause background video"}
                data-testid="hero-pause-toggle"
              >
                {isPaused ? <Play size={17} /> : <Pause size={17} />}
                {isPaused ? "Play Overview" : "Pause Overview"}
              </button>
            ) : null}
          </div>
        </div>
      </div>

      {hasMultipleSlides ? (
        <>
          <button
            type="button"
            className="home-video-hero__arrow home-video-hero__arrow--prev"
            onClick={goToPrevious}
            aria-label="Previous slide"
            data-testid="hero-prev"
          >
            <ChevronLeft size={22} />
          </button>
          <button
            type="button"
            className="home-video-hero__arrow home-video-hero__arrow--next"
            onClick={goToNext}
            aria-label="Next slide"
            data-testid="hero-next"
          >
            <ChevronRight size={22} />
          </button>

          <div
            ref={paginationContainerRef}
            className="home-video-hero__pagination"
            aria-label="Presentation slide navigation"
          >
            {slides.map((slide, index) => (
              <button
                key={slide.id}
                ref={(node) => {
                  paginationRefs.current[slide.id] = node;
                }}
                type="button"
                onClick={() => goToSlide(index)}
                aria-label={`Show slide ${index + 1} of ${slides.length}`}
                aria-current={index === activeIndex ? "true" : undefined}
                data-testid={`hero-pagination-${slide.id}`}
              >
                <span />
              </button>
            ))}
          </div>
        </>
      ) : null}

      <div className="home-video-hero__status" aria-live="polite">
        Slide {activeIndex + 1} of {slides.length}
      </div>
    </section>
  );
}
