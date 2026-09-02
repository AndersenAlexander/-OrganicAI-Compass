import { mockRoadmapView } from "../../data/mockRoadmap";
import { RoadmapColumn } from "./RoadmapColumn";

export function RoadmapTimeline() {
  return (
    <div className="flow-line grid gap-5 lg:grid-cols-3">
      {mockRoadmapView.map((column) => <RoadmapColumn key={column.title} {...column} />)}
    </div>
  );
}
