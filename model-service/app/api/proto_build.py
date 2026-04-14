#!/usr/bin/env python3
import subprocess
import sys
import os

proto_file = os.path.join(os.path.dirname(__file__), "../../../../proto/service.proto")
output_dir = os.path.dirname(__file__)

cmd = [
    "python", "-m", "grpc_tools.protoc",
    f"--python_out={output_dir}",
    f"--grpc_python_out={output_dir}",
    "-I../../../../proto",
    proto_file,
]

print(f"Running: {' '.join(cmd)}")
subprocess.run(cmd)