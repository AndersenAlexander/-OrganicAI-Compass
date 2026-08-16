import type { CSSProperties, VideoHTMLAttributes } from "react";

type ProductDemoVideoProps = {
  src: string;
  poster: string;
  title: string;
  caption?: string;
  className?: string;
  aspectRatio?: string;
  testId?: string;
} & Pick<VideoHTMLAttributes<HTMLVideoElement>, "autoPlay" | "controls" | "loop" | "muted" | "preload">;

export function ProductDemoVideo({
  src,
  poster,
  title,
  caption,
  className = "",
  aspectRatio = "16 / 9",
  testId,
  controls = true,
  autoPlay = false,
  muted = false,
  loop = false,
  preload = "none",
}: ProductDemoVideoProps) {
  return (
    <figure
      className={`product-demo-video ${className}`.trim()}
      data-testid={testId}
      style={{ "--product-demo-aspect": aspectRatio } as CSSProperties}
    >
      <video
        aria-label={title}
        autoPlay={autoPlay}
        controls={controls}
        loop={loop}
        muted={muted}
        playsInline
        poster={poster}
        preload={preload}
        src={src}
      />
      {caption ? <figcaption>{caption}</figcaption> : null}
    </figure>
  );
}
