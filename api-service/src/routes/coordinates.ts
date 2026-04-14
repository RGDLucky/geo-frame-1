import { Router } from "express";
import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const dataPath = path.join(__dirname, "../data/coordinates.json");

export interface Coordinate {
  id: string;
  name: string;
  lat: number;
  lng: number;
  info: string;
}

function loadCoordinates(): Coordinate[] {
  const data = fs.readFileSync(dataPath, "utf-8");
  return JSON.parse(data);
}

export const coordinatesRouter = Router();

coordinatesRouter.get("/", (_req, res) => {
  const coords = loadCoordinates();
  res.json(coords.map(({ id, name, lat, lng }) => ({ id, name, lat, lng })));
});

coordinatesRouter.get("/:id", (req, res) => {
  const coords = loadCoordinates();
  const coord = coords.find((c) => c.id === req.params.id);
  
  if (!coord) {
    res.status(404).json({ error: "Coordinate not found" });
    return;
  }
  
  res.json(coord);
});