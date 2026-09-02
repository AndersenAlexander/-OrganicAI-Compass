import { describe, expect, test } from "vitest";
import { heroVideoSlides } from "./heroVideoSlides";

describe("homepage hero video slide configuration", () => {
  test("keeps the validated homepage message on the first slide", () => {
    const [firstSlide] = heroVideoSlides;

    expect(firstSlide.eyebrow).toBe("HUMAN-CENTRED AI FOR MEANINGFUL ACTION");
    expect(firstSlide.title).toBe("Design your future.");
    expect(firstSlide.highlightedText).toBe("Together with AI.");
    expect(firstSlide.primaryAction).toEqual({ label: "Start Your Diagnostic", to: "/diagnostic" });
    expect(firstSlide.secondaryAction).toEqual({ label: "See How It Works", to: "/how-it-works" });
    expect(firstSlide.tertiaryAction).toEqual({ label: "Explore the Research", to: "/research" });
  });

  test("uses the local homepage videos in the configured presentation order", () => {
    expect(heroVideoSlides.map((slide) => slide.sources[0]?.src)).toEqual([
      "/videos/home/0.%20OrganicAI_Compass_presentation.mp4",
      "/videos/home/1.%20OrganicAI_Compass_presentation_.mp4",
      "/videos/home/2.%20OrganicAI_Compass_final_scene_title.mp4",
      "/videos/home/3.%20OrganicAI_Compass_academic_prese.mp4",
      "/videos/home/4.%20OrganicAI_Compass_diagnostic.mp4",
      "/videos/home/5.%20OrganicAI_Compass_launch.mp4",
      "/videos/home/Career_Experiment_Lab_Evidence.mp4",
      "/videos/home/Cursor_exploring_3D_network_nodes.mp4",
      "/videos/home/Diagnostic_wizard_dashboard.mp4",
      "/videos/home/Documents_linking_to_platform_core.mp4",
      "/videos/home/Human_Potential_Map_interface.mp4",
      "/videos/home/Man_in_office_looking_at.mp4",
      "/videos/home/OrganicAI_Compass_node_selection.mp4",
      "/videos/home/OrganicAI_Compass_presentatio.mp4",
      "/videos/home/OrganicAI_Compass_presentation.mp4",
      "/videos/home/OrganicAI_voice_coach_interface.mp4",
      "/videos/home/Thesis_presentation_OrganicAI_Co%E2%80%A6_202607241945.mp4",
    ]);
  });

  test("supports multiple local video-backed slides without changing slider internals", () => {
    expect(heroVideoSlides.length).toBe(17);

    for (const slide of heroVideoSlides) {
      expect(slide.id).toMatch(/^[a-z0-9-]+$/);
      expect(slide.posterSrc).toMatch(/^\/images\//);
      expect(slide.sources.length).toBeGreaterThan(0);
      for (const source of slide.sources) {
        expect(source.src).toMatch(/^\/videos\/home\//);
        expect(source.type).toMatch(/^video\//);
      }
      expect(slide.objectPosition).toBeTruthy();
      expect(slide.fallbackDurationMs).toBeGreaterThanOrEqual(9000);
    }
  });
});
