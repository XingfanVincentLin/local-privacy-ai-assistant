# Privacy verification

The Phase 3 report should treat privacy as an empirical claim, not only an
architectural claim. The planned test is a packet capture during active local
queries.

## Suggested procedure

1. Download dependencies and Ollama models before the test.
2. Start Home Assistant on the Raspberry Pi as usual.
3. Start the local assistant on the Mac.
4. Run a packet capture on the Mac network interface.
5. Ask a set of benchmark questions through the local web UI.
6. Stop the capture and inspect whether the assistant made external connections
   during query handling.

Example command, to adapt after identifying the correct interface:

```bash
sudo tcpdump -i en0 -n 'not net 192.168.0.0/16 and not net 10.0.0.0/8 and not net 172.16.0.0/12' -w reports/results/privacy_check.pcap
```

The final report should describe the exact interface, filter, duration, and
result. If there is any traffic, it should be explained rather than hidden.

## Supplementary process-level audit

A process-level audit script is included for a repeatable privacy check that
does not require `sudo`:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
python scripts/privacy_connection_audit.py \
  --questions reports/results/privacy_queries.local.json \
  --output reports/results/privacy_connection_audit_scoped.json \
  --benchmark-output reports/results/privacy_connection_audit_scoped_benchmark.csv
```

The script runs representative local benchmark queries with Hugging Face and
Transformers offline flags enabled. During the run it samples `lsof` for the
benchmark process and the local Ollama process only, then records any external
IP connections.

On 2026-06-17, the scoped audit monitored 74 samples while five local queries
ran through Ollama. It recorded 0 external IP observations for the monitored
benchmark/Ollama processes. The corresponding local result files are kept under
`reports/results/` and are ignored by Git.

This audit is useful supporting evidence, but it is not a full packet capture.
For the strongest final claim, run the `tcpdump` test manually in Terminal with
your macOS password and include the resulting packet count or finding in the
Phase 3 report.
