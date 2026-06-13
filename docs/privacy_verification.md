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

