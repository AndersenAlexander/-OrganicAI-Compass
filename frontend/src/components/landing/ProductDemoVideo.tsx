import { Maximize2, Pause, Play, Volume2, VolumeX } from "lucide-react";
import { useEffect, useRef, useState, type CSSProperties, type ChangeEvent, type VideoHTMLAttributes } from "react";

type ProductDemoVideoProps = {
  src: string;
  poster: string;
  title: string;
  caption?: string;
  className?: string;
  aspectRatio?: string;
  testId?: string;
  showControls?: boolean;
} & Pick<VideoHTMLAttributes<HTMLVideoElement>, "autoPlay" | "controls" | "loop" | "muted" | "preload">;

function formatTime(value: number) {
  if (!Number.isFinite(value) || value < 0) return "0:00";
  const minutes = Math.floor(value / 60);
  const seconds = Math.floor(value % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export function ProductDemoVideo({
  src,
  poster,
  title,
  caption,
  className = "",
  aspectRatio = "16 / 9",
  testId,
  showControls = true,
  controls = false,
  autoPlay = false,
  muted = false,
  loop = false,
  preload = "none",
}: ProductDemoVideoProps) {
  const frameRef = useRef<HTMLDivElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(muted);
  const [volume, setVolume] = useState(1);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const syncPlayback = () => setIsPlaying(!video.paused && !video.ended);
    const syncMetadata = () => setDuration(Number.isFinite(video.duration) ? video.duration : 0);
    const syncTime = () => setCurrentTime(video.currentTime);
    const syncVolume = () => {
      setIsMuted(video.muted);
      setVolume(video.volume);
    };

    video.volume = 1;
    video.muted = muted;
    syncPlayback();
    syncMetadata();
    syncTime();
    syncVolume();
    video.addEventListener("play", syncPlayback);
    video.addEventListener("pause", syncPlayback);
    video.addEventListener("ended", syncPlayback);
    video.addEventListener("loadedmetadata", syncMetadata);
    video.addEventListener("durationchange", syncMetadata);
    video.addEventListener("timeupdate", syncTime);
    video.addEventListener("volumechange", syncVolume);

    return () => {
      video.removeEventListener("play", syncPlayback);
      video.removeEventListener("pause", syncPlayback);
      video.removeEventListener("ended", syncPlayback);
      video.removeEventListener("loadedmetadata", syncMetadata);
      video.removeEventListener("durationchange", syncMetadata);
      video.removeEventListener("timeupdate", syncTime);
      video.removeEventListener("volumechange", syncVolume);
    };
  }, [muted, src]);

  useEffect(() => {
    const syncFullscreen = () => setIsFullscreen(document.fullscreenElement === frameRef.current);
    document.addEventListener("fullscreenchange", syncFullscreen);
    return () => document.removeEventListener("fullscreenchange", syncFullscreen);
  }, []);

  const togglePlayback = async () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused || video.ended) {
      if (video.ended) video.currentTime = 0;
      try {
        await video.play();
      } catch {
        setIsPlaying(false);
      }
      return;
    }
    video.pause();
  };

  const toggleMute = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.muted && video.volume === 0) {
      video.volume = 0.65;
      setVolume(0.65);
    }
    video.muted = !video.muted;
    setIsMuted(video.muted);
  };

  const handleVolumeChange = (event: ChangeEvent<HTMLInputElement>) => {
    const nextVolume = Number(event.currentTarget.value);
    const video = videoRef.current;
    setVolume(nextVolume);
    if (!video) return;
    video.volume = nextVolume;
    video.muted = nextVolume === 0;
    setIsMuted(video.muted);
  };

  const handleSeek = (event: ChangeEvent<HTMLInputElement>) => {
    const nextTime = Number(event.currentTarget.value);
    setCurrentTime(nextTime);
    if (videoRef.current) videoRef.current.currentTime = nextTime;
  };

  const toggleFullscreen = () => {
    const frame = frameRef.current;
    if (!frame) return;
    if (document.fullscreenElement) {
      void document.exitFullscreen();
      return;
    }
    void frame.requestFullscreen?.();
  };

  return (
    <figure
      className={`product-demo-video ${className}`.trim()}
      data-testid={testId}
      style={{ "--product-demo-aspect": aspectRatio } as CSSProperties}
    >
      <div className="product-demo-video__frame" ref={frameRef}>
        <video
          ref={videoRef}
          aria-label={title}
          autoPlay={autoPlay}
          controls={controls}
          loop={loop}
          muted={isMuted}
          playsInline
          poster={poster}
          preload={preload}
          src={src}
        />
        {showControls ? (
          <div className="product-demo-video__controls" aria-label={`${title} video controls`}>
            <div className="product-demo-video__control-row">
              <button
                type="button"
                className="product-demo-video__icon-button"
                aria-label={isPlaying ? "Pause video" : "Play video"}
                title={isPlaying ? "Pause video" : "Play video"}
                onClick={() => void togglePlayback()}
              >
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
              </button>
              <button
                type="button"
                className="product-demo-video__icon-button"
                aria-label={isMuted ? "Unmute video" : "Mute video"}
                title={isMuted ? "Unmute video" : "Mute video"}
                onClick={toggleMute}
              >
                {isMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
              </button>
              <label className="product-demo-video__volume-control">
                <span className="sr-only">Volume</span>
                <input
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  value={isMuted ? 0 : volume}
                  aria-label="Volume"
                  onChange={handleVolumeChange}
                />
              </label>
              <span className="product-demo-video__time" aria-live="off">
                {formatTime(currentTime)} / {formatTime(duration)}
              </span>
              <button
                type="button"
                className="product-demo-video__icon-button"
                aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
                title={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
                onClick={toggleFullscreen}
              >
                <Maximize2 size={16} />
              </button>
            </div>
            <label className="product-demo-video__progress-control">
              <span className="sr-only">Video progress</span>
              <input
                type="range"
                min="0"
                max={duration || 0}
                step="0.1"
                value={Math.min(currentTime, duration || 0)}
                aria-label="Video progress"
                onChange={handleSeek}
              />
            </label>
          </div>
        ) : null}
      </div>
      {caption ? <figcaption>{caption}</figcaption> : null}
    </figure>
  );
}
