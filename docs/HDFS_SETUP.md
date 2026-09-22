# Hadoop / HDFS Pseudo-Distributed Cluster Setup (Person 1)

Person 1's ingestion layer lands raw listing batches in HDFS under `/data/raw/`
via [`hdfs_uploader.py`](../hdfs_uploader.py). This guide sets up the local
pseudo-distributed Hadoop cluster that `hdfs_uploader.py` targets, and pairs
with [`SPARK_SETUP.md`](SPARK_SETUP.md) (Person 2) for the processing layer.

> Companion deliverable: `python -m scraper.validator` then
> `python -m scraper.jsonl_converter` close the Person 1 → Person 2 handoff.

---

## 1. Prerequisites

| Component | Version | Notes |
| --------- | ------- | ----- |
| Java      | JDK 8 or 11 | Hadoop 3.x runs best on 8/11 (Person 2's Spark uses Java 19 separately) |
| Hadoop    | 3.3.x   | Binary tarball from https://hadoop.apache.org/releases.html |
| OS        | Windows / Linux | Windows needs `winutils.exe` + `hadoop.dll` matching the Hadoop version |

Unzip/extract Hadoop to a directory, e.g. `C:\hadoop` (Windows) or
`/opt/hadoop` (Linux). On Windows also place `winutils.exe` and `hadoop.dll`
in `C:\hadoop\bin`.

---

## 2. Environment Variables

PowerShell (Windows):

```powershell
$env:JAVA_HOME = "C:\Program Files\Java\jdk-11"
$env:HADOOP_HOME = "C:\hadoop"
$env:HADOOP_CONF_DIR = "C:\hadoop\etc\hadoop"
$env:PATH = "C:\hadoop\bin;$env:PATH"
```

Linux (bash):

```bash
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk
export HADOOP_HOME=/opt/hadoop
export PATH=$HADOOP_HOME/bin:$PATH
```

Verify:

```bash
hadoop version
```

---

## 3. Core Configuration Files (`etc/hadoop/`)

### `core-site.xml`

```xml
<configuration>
  <property>
    <name>fs.defaultFS</name>
    <value>hdfs://localhost:9000</value>
  </property>
</configuration>
```

### `hdfs-site.xml`

```xml
<configuration>
  <property>
    <name>dfs.replication</name>
    <value>1</value>
  </property>
  <property>
    <name>dfs.namenode.name.dir</name>
    <value>file:///C:/hadoop/data/namenode</value>
  </property>
  <property>
    <name>dfs.datanode.data.dir</name>
    <value>file:///C:/hadoop/data/datanode</value>
  </property>
  <property>
    <name>dfs.webhdfs.enabled</name>
    <value>true</value>
  </property>
</configuration>
```

`dfs.webhdfs.enabled=true` is required — `hdfs_uploader.py` prefers the
WebHDFS REST API on port **9870** (Hadoop 3.x).

### `mapred-site.xml` / `yarn-site.xml`

Not required for this pipeline (HDFS storage only); Spark runs `local[*]`.

---

## 4. Format the NameNode & Start Daemons

First start only (skippable afterwards):

```bash
hdfs namenode -format
```

Start the cluster:

```bash
# Windows:
%HADOOP_HOME%\sbin\start-dfs.cmd
# Linux:
$HADOOP_HOME/sbin/start-dfs.sh
```

Verify — NameNode web UI at http://localhost:9870 should show live datanodes:

```bash
hdfs dfsadmin -report
hdfs dfs -mkdir -p /data/raw
hdfs dfs -ls /data
```

---

## 5. Push the Raw Data Lake to HDFS

```bash
python hdfs_uploader.py
```

`hdfs_uploader.py` auto-detects, in order:
1. **WebHDFS** (`http://localhost:9870`) — used when the NameNode is live
2. **HDFS CLI** (`hdfs dfs -put`) — fallback
3. **Pseudo-HDFS emulation** — catalogs files locally with a sync manifest
   (`data/hdfs_sync_manifest.json`) when no daemons are running

Files already pushed are tracked in the manifest, so re-running is idempotent.

---

## 6. Full Ingestion Deliverable Run (50k+ listings)

```bash
# 1. Generate the raw batches (50,000+ listings into data/raw/)
python -c "from scraper.generator import generate_batch; generate_batch(count=50000, category='all')"

# 2. Validate against the schema contract (quality gate)
python -m scraper.validator

# 3. Push raw JSON to HDFS /data/raw/
python hdfs_uploader.py

# 4. Convert raw JSON -> JSONL for Person 2's Spark pipeline
python -m scraper.jsonl_converter
# -> data/processed/raw_listings.jsonl
```

Step 4 output is the exact input path Person 2's
`spark_jobs/clean_normalize.py` expects — the joint Person 1 → Person 2
checkpoint is now a two-command step.

---

## 7. Troubleshooting

| Symptom | Fix |
| ------- | --- |
| `hdfs_uploader.py` reports `EMULATED_MODE` | NameNode not running or WebHDFS disabled — check http://localhost:9870 and `dfs.webhdfs.enabled` |
| Datanode starts then dies (Windows) | `winutils.exe`/`hadoop.dll` version mismatch with Hadoop, or `JAVA_HOME` unset |
| `dfs.namenode.name.dir` permission errors | Pre-create the dirs and use forward-slash `file:///` URIs exactly as above |
| WebHDFS 403 on upload | Ensure `hdfs dfs -mkdir -p /data/raw` was run and the `user` in `hdfs_uploader.py` has write access |
| Manifest says pushed but HDFS empty | Manifest is local state — delete `data/hdfs_sync_manifest.json` and re-run to force a clean sync |
