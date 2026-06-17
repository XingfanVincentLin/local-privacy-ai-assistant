from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import select
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


IP_PATTERN = re.compile(r"(?<![\w:])(?:\d{1,3}\.){3}\d{1,3}(?![\w:])|[0-9a-fA-F:]{2,}")


def is_external_ip(value: str) -> bool:
    try:
        address = ipaddress.ip_address(value.strip("[]"))
    except ValueError:
        return False
    return not (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
        or address.is_reserved
    )


def external_ips_from_lsof_line(line: str) -> list[str]:
    matches = []
    for raw_value in IP_PATTERN.findall(line):
        if is_external_ip(raw_value):
            matches.append(raw_value)
    return matches


def ollama_pids() -> set[int]:
    result = subprocess.run(
        ["pgrep", "-x", "ollama"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    return {int(line) for line in result.stdout.splitlines() if line.strip().isdigit()}


def sample_lsof(pids: set[int]) -> list[dict]:
    if not pids:
        return []
    result = subprocess.run(
        ["lsof", "-nP", "-a", "-p", ",".join(str(pid) for pid in sorted(pids)), "-iTCP", "-iUDP"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    observations = []
    for line in result.stdout.splitlines()[1:]:
        external_ips = external_ips_from_lsof_line(line)
        if external_ips:
            observations.append({"line": line, "external_ips": sorted(set(external_ips))})
    return observations


def run_audit(args: argparse.Namespace) -> int:
    output_path = Path(args.output)
    benchmark_output_path = Path(args.benchmark_output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    benchmark_output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        sys.executable,
        "scripts/eval_benchmark.py",
        "--questions",
        args.questions,
        "--output",
        str(benchmark_output_path),
        "--timeout-seconds",
        str(args.timeout_seconds),
    ]
    env = os.environ.copy()
    env.update(
        {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
            "PYTHONUNBUFFERED": "1",
        }
    )

    started_at = datetime.now(timezone.utc).isoformat()
    process = subprocess.Popen(
        command,
        cwd=ROOT,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    samples = []
    benchmark_output = []
    while process.poll() is None:
        if process.stdout:
            while select.select([process.stdout], [], [], 0)[0]:
                line = process.stdout.readline()
                if not line:
                    break
                benchmark_output.append(line.rstrip())
                print(line, end="")
        monitored_pids = {process.pid} | ollama_pids()
        observations = sample_lsof(monitored_pids)
        samples.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "monitored_pids": sorted(monitored_pids),
                "external_observations": observations,
            }
        )
        time.sleep(args.sample_interval)

    if process.stdout:
        remaining = process.stdout.read()
        if remaining:
            for line in remaining.splitlines():
                benchmark_output.append(line)
                print(line)

    ended_at = datetime.now(timezone.utc).isoformat()
    external_observations = [
        {"timestamp": sample["timestamp"], **observation}
        for sample in samples
        for observation in sample["external_observations"]
    ]
    report = {
        "started_at": started_at,
        "ended_at": ended_at,
        "command": command,
        "offline_environment": {
            "HF_HUB_OFFLINE": "1",
            "TRANSFORMERS_OFFLINE": "1",
        },
        "sample_interval_seconds": args.sample_interval,
        "sample_count": len(samples),
        "monitored_pids": sorted({pid for sample in samples for pid in sample["monitored_pids"]}),
        "external_observation_count": len(external_observations),
        "external_observations": external_observations,
        "benchmark_exit_code": process.returncode,
        "benchmark_output_path": str(benchmark_output_path),
        "benchmark_output_tail": benchmark_output[-20:],
        "method_note": (
            "This is a process-level lsof audit for external IP connections during local "
            "benchmark queries. It supplements, but does not replace, a sudo tcpdump packet "
            "capture on the active network interface."
        ),
    }
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {output_path}")
    print(f"External observations: {len(external_observations)}")
    return process.returncode or 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit external connections during local RAG queries.")
    parser.add_argument("--questions", default="reports/results/privacy_queries.local.json")
    parser.add_argument("--output", default="reports/results/privacy_connection_audit.json")
    parser.add_argument(
        "--benchmark-output",
        default="reports/results/privacy_connection_audit_benchmark.csv",
    )
    parser.add_argument("--timeout-seconds", type=float, default=45.0)
    parser.add_argument("--sample-interval", type=float, default=0.5)
    raise SystemExit(run_audit(parser.parse_args()))


if __name__ == "__main__":
    main()
