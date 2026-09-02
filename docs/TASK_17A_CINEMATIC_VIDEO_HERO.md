# TASK 17A - Cinematic Video Hero Slider

## Scope

This change is frontend presentation only. It replaces the constrained homepage hero with a full-viewport-width video slider while keeping normal homepage content in the existing centered container.

No backend logic, authentication, privacy architecture, schema, migration, provider configuration, or release version was changed.

## Previous Structure

The homepage route is `/` and renders `frontend/src/pages/LandingPage.tsx`.

Before this task, `LandingPage.tsx` defined an inline `HomeHero()` function and rendered it inside `.home-page-container`. The page also sits inside `PublicLayout`, whose `<main>` has a max width and horizontal padding. Those wrappers made the old hero visually constrained.

## New Architecture

The hero is now rendered by:

`frontend/src/components/landing/HeroVideoSlider.tsx`

The slide data is defined in:

`frontend/src/config/heroVideoSlides.ts`

`LandingPage.tsx` renders `HeroVideoSlider` before the centered `.home-page-container`. The homepage overrides the public `<main>` max-width only when `.home-page` is present, so the slider is not constrained by the normal page container. The visual media spans `100vw`, while `.home-video-hero__content` keeps text and CTAs aligned to a readable internal grid.

The four platform pillars remain immediately below the hero and keep the existing copy:

- Understand Yourself
- Ground AI in Knowledge
- Turn Insight into Action
- Grow with Confidence

## Video Directory

Place homepage presentation videos in:

`frontend/public/videos/home/`

The configured filenames are:

- `0. OrganicAI_Compass_presentation.mp4`
- `1. OrganicAI_Compass_presentation_.mp4`
- `2. OrganicAI_Compass_final_scene_title.mp4`
- `3. OrganicAI_Compass_academic_prese.mp4`
- `4. OrganicAI_Compass_diagnostic.mp4`
- `5. OrganicAI_Compass_launch.mp4`
- `Career_Experiment_Lab_Evidence.mp4`
- `Cursor_exploring_3D_network_nodes.mp4`
- `Diagnostic_wizard_dashboard.mp4`
- `Documents_linking_to_platform_core.mp4`
- `Human_Potential_Map_interface.mp4`
- `Man_in_office_looking_at.mp4`
- `OrganicAI_Compass_node_selection.mp4`
- `OrganicAI_Compass_presentatio.mp4`
- `OrganicAI_Compass_presentation.mp4`
- `OrganicAI_voice_coach_interface.mp4`
- `Thesis_presentation_OrganicAI_Co…_202607241945.mp4`

The repository originally tracked the directory with `.gitkeep` only. The slider configuration now points to the local presentation files listed above.

## Adding Another Video

1. Copy the optimized video into `frontend/public/videos/home/`.
2. Open `frontend/src/config/heroVideoSlides.ts`.
3. Add one object to `heroVideoSlides` with `id`, `sources`, `posterSrc`, text, actions, and optional `objectPosition`.

No edits to `HeroVideoSlider.tsx` should be needed.

## Playback Behavior

Videos start muted and use `playsInline`.

Only the active slide is asked to play. Inactive videos are paused and reset to the beginning when they leave the active slide.

Finite videos advance on the native `ended` event. If a video is unavailable, blocked, data-saving mode is enabled, or a slide uses `advanceAfterMs`, the slider uses the slide fallback duration instead.

The pause/play control toggles background playback and has accessible labels.

## Slider Controls

The left and right arrows are positioned absolutely against the full-width hero surface, not inside the text container:

- previous slide: left viewport edge, vertical center
- next slide: right viewport edge, vertical center

The slide navigation is a segmented horizontal bar positioned at the bottom center of the hero. Each segment is clickable and the active slide segment is longer and brighter.

## TASK 17B Simplified Hero Content

The visible hero overlay is intentionally minimal so the videos remain the primary storytelling element.

Visible homepage overlay:

- `Welcome to OrganicAI Compass`
- `Start Your Diagnostic`
- `See How It Works`
- `Play Overview` / `Pause Overview`

Slide-specific titles, highlighted text, descriptions, and tertiary links remain in `heroVideoSlides.ts` for future modes, but the default homepage hero does not render them. The component supports a simple `contentMode` prop so a later iteration can move from `welcome` mode to an even more minimal `actions-only` mode without rewriting the slider internals.

The overlay gradient was reduced from a heavy left-side readability layer to a lighter cinematic darkening plus bottom gradient for CTA/control contrast.

## Accessibility

Background videos are treated as decorative media. Text, CTAs, arrows, pagination, and the pause/play control remain keyboard-accessible.

Pagination buttons announce slide number and slide title. The current slide is exposed through `aria-current`.

## Reduced Motion

When `prefers-reduced-motion: reduce` is active, video sources are not loaded automatically, autoplay is paused, and automatic slide progression is disabled. Manual navigation remains available and content stays visible over poster images.

## Mobile Behavior

The hero remains full viewport width on mobile, with a shorter viewport-based height, tighter typography, stacked CTAs on narrow screens, accessible control hit areas, and per-slide `objectPosition` support for video cropping.

## Light And Dark Mode

The hero uses its own dark adaptive overlay for contrast in both themes. The cards below keep their existing light/dark theme behavior.

## Performance Recommendations

Use locally hosted static files. Avoid third-party embeds for the hero.

Recommended encoding:

- MP4 / H.264 for broad browser support
- Optional WebM alternative for the first slide
- 1080p maximum for background presentation videos
- Optimized bitrate and reasonable file size
- Avoid embedding videos into JavaScript bundles

The component uses `preload="metadata"` only for the active slide and `preload="none"` for inactive slides.

## Fallback Behavior

Each slide supports `posterSrc`. If video loading fails, the poster remains visible, content and CTAs stay usable, and the slider can continue using the fallback duration.
