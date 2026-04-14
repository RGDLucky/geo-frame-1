import dotenv from "dotenv";
dotenv.config();

export const config = {
  appName: process.env.APP_NAME || "api-service",
  port: parseInt(process.env.PORT || "8000", 10),
  modelServiceUrl: process.env.MODEL_SERVICE_URL || "localhost:50051",
  corsOrigins: process.env.CORS_ORIGINS?.split(",") || ["*"],
};