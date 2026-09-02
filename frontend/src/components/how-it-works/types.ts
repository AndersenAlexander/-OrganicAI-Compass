import type { LucideIcon } from "lucide-react";

export type StageAccent = "teal" | "cyan" | "green" | "violet" | "gold" | "lime";

export type JourneyStage = {
  id: string;
  number: string;
  shortTitle: string;
  title: string;
  cardTitle?: string;
  description: string;
  cardDescription?: string;
  exampleLabel: string;
  examples: string[];
  action: string;
  to: string;
  icon: LucideIcon;
  accent: StageAccent;
};

export type PipelineLayer = {
  title: string;
  labels: string[];
  description: string;
  icon: LucideIcon;
};
