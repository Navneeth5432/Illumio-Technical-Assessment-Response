# Illumio-Technical-Assessment-Response
Tool that reads an AWS Flow Log,
applies a **(dstport, protocol) → tag** mapping from a CSV lookup table, and emits two
CSV reports:

1. **`tag_counts.csv`** – how many rows matched each tag (rows with no match are lumped
   under `Untagged`)
2. **`port_protocol_counts.csv`** – how many rows for each unique port + protocol combo

There is a short write-up pdf in the repo detailing the development process, and what was done to avoid certain pitfalls and to improve the program.
## Assumptions



1. Supports **default** VPC Flow Log **version 2** only
2. Lookup CSV has header `dstport,protocol,tag` (any ordering of rows)
3. `protocol` column uses **case-insensitive names** `tcp`, `udp`, `icmp`
4. Flow-log file ≤ 10 MB / ≈ 100 k rows
5. Unknown or unmapped `(dstport,protocol)` pairs are counted as `Untagged`

## Usage
Run this command in the directory where you clone the repo

```bash
python flow_tagger.py <flow_log_file> <lookup_csv> <output_folder>
```
CSV reports will be located in the specified output directory. Initial test inputs are already located in the `tests` directory, so feel free to utilize those as well.

## Test suites
To help with the review the repo comes with **four miniature flow‑log fixtures** and **two lookup tables**. Feel free to compare program’s output against the expected CSVs under `expected_out`.

| File | Scenario & What it proves                                                          |
|------|------------------------------------------------------------------------------------|
| **`test_log_1`** | The example log given with the problem                                             |
| **`test_log_2`** | *Duplicates and basic tally* - multiple records hit the same `(dstport,protocol)`. |
| **`test_log_3`** | *Protocol variety* - contains UDP and ICMP in addition to TCP.                     |
| **`test_log_4`** | *Edge Cases* - Malformed lines, version 3 record, unrecognized protocol            |
| **`test_lookup_1`** | The example lookup table given with the problem                                    |
| **`test_lookup_2`** | Same as first lookup table but with mixed casing and extra whitespace              |

The expected folders are categorized as such:


| Test ID | Flow‑log file | Lookup file     | Scenario & what it proves                                                                                                                                                                |
|---------|---------------|-----------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| **test1** | `test_log_1` | `test_lookup_1` | *Baseline sample* – Uses inputs from original problem                                                                                                                                    |
| **test2** | `test_log_2` | `test_lookup_2` | *Duplicates & tallying* – multiple records hit the same `(dstport, protocol)`. Verifies counters aggregate (e.g. 25/tcp appears twice → `sv_P1,2`).                                      |
| **test3** | `test_log_3` | `test_lookup_2` | *Protocol variety* – mixes UDP and ICMP with TCP. Proves number→name mapping.                                                                                                            |
| **test4** | `test_log_4` | `test_lookup_2` | *Edge cases & stress* – unknown protocol 47, malformed line, version 3 record. Checks unknown protocols remain numeric, malformed rows are skipped, and unsupported versions are skipped |

Run a fixture like so:
```bash
python flow_tagger.py tests/<flow_log_file> tests/<lookup_csv> <output_folder>
```
Then compare against the expected files:
```bash
Compare-Object (Get-Content <output-folder>/tag_counts.csv) (Get-Content .\expected_out\<test_num>\expected_tag_counts.csv)
```
If the diff is empty, then that test has passed