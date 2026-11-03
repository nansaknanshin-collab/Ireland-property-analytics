"""Run the whole pipeline: python run_pipeline.py [--sample]"""
import subprocess
import sys

sample = ["--sample"] if "--sample" in sys.argv else []
steps = ([[sys.executable, "src/make_sample.py"]] if sample else []) + [
    [sys.executable, "src/clean.py", *sample],
    [sys.executable, "src/load_and_analyse.py"],
]
for step in steps:
    print(f"\n>>> {' '.join(step[1:])}")
    subprocess.run(step, check=True)
