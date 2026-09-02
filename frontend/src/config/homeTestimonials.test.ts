import { describe, expect, test } from "vitest";
import { homeTestimonials } from "./homeTestimonials";

describe("homepage testimonials", () => {
  test("does not ship fabricated testimonial content", () => {
    expect(homeTestimonials).toEqual([]);
  });
});
