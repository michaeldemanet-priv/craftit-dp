# Offline reference fixtures

A local run has no server. When `calculator.yaml` declares a reference, put a file here named
after its key:

```text
fixtures/references/<key>.jsonl
fixtures/references/<key>.csv
```

JSONL is one object per line (the protocol's record value encoding). CSV is a header row plus
data rows. The local runner loads the file at the version the manifest pins.

A reference the manifest declares with neither a fixture nor a login fails, naming the key and
both sources it tried. An empty table is never invented.
