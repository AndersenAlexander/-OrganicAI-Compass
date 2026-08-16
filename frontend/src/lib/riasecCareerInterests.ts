export type RiasecDimensionKey = "realistic" | "investigative" | "artistic" | "social" | "enterprising" | "conventional";

export type RiasecDimension = {
  key: RiasecDimensionKey;
  code: string;
  label: string;
  description: string;
  score: number | null;
  band: string;
  directItems: number;
  indirectItems: number;
  weakItems: number;
};

export type RiasecCareerInterestProfile = {
  model: string;
  ruleSetVersion: string;
  status: string;
  dimensions: RiasecDimension[];
  topPattern: string;
  topDimensions: RiasecDimensionKey[];
  closeScoreNotice: string;
  limitations: string[];
};

export const riasecDimensionOrder: RiasecDimensionKey[] = [
  "realistic",
  "investigative",
  "artistic",
  "social",
  "enterprising",
  "conventional",
];

function asRecord(value: unknown): Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

export function extractRiasecCareerInterests(snapshot: Record<string, unknown> | undefined): RiasecCareerInterestProfile | null {
  const careerInterests = asRecord(snapshot?.career_interests);
  const rawDimensions = asRecord(careerInterests.dimensions);
  if (!Object.keys(rawDimensions).length) return null;

  const dimensions = riasecDimensionOrder.map((key) => {
    const item = asRecord(rawDimensions[key]);
    return {
      key,
      code: String(item.code || key[0].toUpperCase()),
      label: String(item.label || key.replace(/_/g, " ")),
      description: String(item.description || ""),
      score: asNumber(item.score),
      band: String(item.band || "Insufficient information"),
      directItems: Number(item.direct_items || 0),
      indirectItems: Number(item.indirect_items || 0),
      weakItems: Number(item.weak_items || 0),
    };
  });

  return {
    model: String(careerInterests.model || "RIASEC-inspired Career Interests"),
    ruleSetVersion: String(careerInterests.rule_set_version || ""),
    status: String(careerInterests.status || "insufficient_information"),
    dimensions,
    topPattern: String(careerInterests.top_pattern || ""),
    topDimensions: Array.isArray(careerInterests.top_dimensions)
      ? careerInterests.top_dimensions.filter((item): item is RiasecDimensionKey => riasecDimensionOrder.includes(item as RiasecDimensionKey))
      : [],
    closeScoreNotice: String(careerInterests.close_score_notice || ""),
    limitations: Array.isArray(careerInterests.limitations) ? careerInterests.limitations.map(String) : [],
  };
}

export function riasecStatusCopy(profile: RiasecCareerInterestProfile | null) {
  if (!profile || profile.status === "insufficient_information") {
    return "Complete Natural Discovery to generate Career Interests.";
  }
  if (profile.status === "derived_from_legacy") {
    return "Derived from earlier Natural Discovery answers; retake Natural Discovery for balanced direct responses.";
  }
  return "Generated from current Natural Discovery career-interest responses.";
}
