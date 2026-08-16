import { expect, type Locator } from "@playwright/test";

export type ContrastSample = {
  color: string;
  backgroundColor: string;
  ratio: number;
  text: string;
};

export function luminance([red, green, blue]: [number, number, number]) {
  const linear = [red, green, blue].map((channel) => {
    const normalized = channel / 255;
    return normalized <= 0.03928 ? normalized / 12.92 : Math.pow((normalized + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}

export function contrastRatio(foreground: [number, number, number], background: [number, number, number]) {
  const first = luminance(foreground);
  const second = luminance(background);
  return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
}

export async function sampleContrast(locator: Locator): Promise<ContrastSample> {
  return locator.first().evaluate((element) => {
    type Rgba = [number, number, number, number];

    const parseColor = (value: string): Rgba | null => {
      const channels = value.match(/[\d.]+/g)?.map(Number);
      if (!channels || channels.length < 3) return null;
      if (value.trim().startsWith("color(srgb")) {
        return [channels[0] * 255, channels[1] * 255, channels[2] * 255, channels[3] ?? 1];
      }
      return [channels[0], channels[1], channels[2], channels[3] ?? 1];
    };

    const blend = (top: Rgba, bottom: Rgba): Rgba => {
      const alpha = top[3] + bottom[3] * (1 - top[3]);
      if (alpha === 0) return [255, 255, 255, 1];
      return [
        (top[0] * top[3] + bottom[0] * bottom[3] * (1 - top[3])) / alpha,
        (top[1] * top[3] + bottom[1] * bottom[3] * (1 - top[3])) / alpha,
        (top[2] * top[3] + bottom[2] * bottom[3] * (1 - top[3])) / alpha,
        alpha,
      ];
    };

    const relativeLuminance = ([red, green, blue]: [number, number, number]) => {
      const linear = [red, green, blue].map((channel) => {
        const normalized = channel / 255;
        return normalized <= 0.03928 ? normalized / 12.92 : Math.pow((normalized + 0.055) / 1.055, 2.4);
      });
      return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
    };

    const ratio = (foreground: [number, number, number], background: [number, number, number]) => {
      const first = relativeLuminance(foreground);
      const second = relativeLuminance(background);
      return (Math.max(first, second) + 0.05) / (Math.min(first, second) + 0.05);
    };

    const foreground = parseColor(getComputedStyle(element).color) ?? [0, 0, 0, 1];
    let background: Rgba = [255, 255, 255, 1];
    let current: Element | null = element;

    while (current) {
      const computed = getComputedStyle(current);
      const parsed = parseColor(computed.backgroundColor);
      if (parsed && parsed[3] > 0) background = blend(parsed, background);
      if (parsed && parsed[3] >= 0.98) break;
      current = current.parentElement;
    }

    const gradientColors = Array.from(getComputedStyle(element).backgroundImage.matchAll(/rgba?\([^)]+\)/g))
      .map((match) => parseColor(match[0]))
      .filter(Boolean) as Rgba[];
    const solidRatio = ratio([foreground[0], foreground[1], foreground[2]], [background[0], background[1], background[2]]);
    const gradientRatios = gradientColors.map((color) => {
      const blended = color[3] < 1 ? blend(color, background) : color;
      return ratio([foreground[0], foreground[1], foreground[2]], [blended[0], blended[1], blended[2]]);
    });

    return {
      color: getComputedStyle(element).color,
      backgroundColor: gradientColors.length
        ? `gradient over rgb(${Math.round(background[0])}, ${Math.round(background[1])}, ${Math.round(background[2])})`
        : `rgb(${Math.round(background[0])}, ${Math.round(background[1])}, ${Math.round(background[2])})`,
      ratio: gradientRatios.length ? Math.min(...gradientRatios) : solidRatio,
      text: element.textContent?.replace(/\s+/g, " ").trim() ?? "",
    };
  });
}

export async function expectContrast(locator: Locator, minimum = 4.5) {
  await expect(locator.first()).toBeVisible();
  const sample = await sampleContrast(locator);
  expect(sample.ratio, `${sample.text || "element"} contrast ${sample.color} on ${sample.backgroundColor}`).toBeGreaterThanOrEqual(minimum);
  return sample;
}
