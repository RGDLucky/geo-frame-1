import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";
import { config } from "./config.js";
import { router } from "./routes/index.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const frontendDist = path.resolve(__dirname, "../../frontend/dist");

const app = express();

app.use(cors({ origin: config.corsOrigins }));
app.use(express.json());

app.use(express.static(frontendDist, { index: false }));

app.use("/api/", router);

app.get("/health", (_req, res) => {
  res.json({ status: "healthy" });
});

app.get("*", (_req, res) => {
  res.sendFile(path.join(frontendDist, "index.html"));
});

app.listen(config.port, () => {
  console.log(`${config.appName} running on port ${config.port}`);
});