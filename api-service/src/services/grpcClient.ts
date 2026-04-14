import * as grpc from "@grpc/grpc-js";
import * as protoLoader from "@grpc/proto-loader";
import { config } from "../config.js";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const protoPath = path.resolve(__dirname, "../../proto/service.proto");

let packageDefinition: protoLoader.PackageDefinition;
let proto: any;

async function loadProto() {
  if (!packageDefinition) {
    packageDefinition = await protoLoader.load(protoPath, {
      keepCase: false,
      longs: String,
      enums: String,
      defaults: true,
      oneofs: true,
    });
    proto = grpc.loadPackageDefinition(packageDefinition);
  }
  return proto;
}

export async function getModelServiceClient() {
  const loadedProto = await loadProto();
  const stub = new loadedProto.ModelService(
    config.modelServiceUrl,
    grpc.credentials.createInsecure()
  );
  return stub;
}