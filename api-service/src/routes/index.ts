import { Router } from "express";
import { coordinatesRouter } from "./coordinates.js";

export const router = Router();

router.get("/", (_req, res) => {
  res.json({ message: "API Service" });
});

router.use("/coordinates", coordinatesRouter);