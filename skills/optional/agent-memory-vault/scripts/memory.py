#!/usr/bin/env python3
"""Persistent JSONL-backed memory for autonomous agents.

Usage:
  python memory.py put --topic=X --key=Y --value=Z
  python memory.py get --topic=X --key=Y
  python memory.py list [--topic=X]
  python memory.py context --last=10
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

DEFAULT_HOME = "~/.agent-memory"

def memory_home():
    return Path(os.environ.get("AGENT_MEMORY_HOME", DEFAULT_HOME)).expanduser()

def topic_path(topic):
    home = memory_home()
    home.mkdir(parents=True, exist_ok=True)
    return home / (topic + ".jsonl")

def index_path():
    return memory_home() / "index.json"

def load_index():
    p = index_path()
    if not p.exists():
        return {"topics": {}}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {"topics": {}}

def save_index(idx):
    p = index_path()
    p.write_text(json.dumps(idx, indent=2))

def append_entry(topic, key, value, ts=None):
    ts = ts or int(time.time())
    entry = {"ts": ts, "key": key, "value": value}
    p = topic_path(topic)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    idx = load_index()
    if topic not in idx["topics"]:
        idx["topics"][topic] = {"count": 0, "last_ts": 0}
    idx["topics"][topic]["count"] += 1
    idx["topics"][topic]["last_ts"] = ts
    save_index(idx)
    print("[memory] " + topic + "/" + key + " = " + repr(value))

def get_entry(topic, key, latest=True):
    p = topic_path(topic)
    if not p.exists():
        return None
    entries = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
    matches = [e for e in entries if e.get("key") == key]
    if not matches:
        return None
    return matches[-1] if latest else matches

def list_topic(topic=None):
    idx = load_index()
    if topic:
        p = topic_path(topic)
        if not p.exists():
            print("[memory] No topic: " + topic)
            return
        count = idx['topics'].get(topic, {}).get('count', 0)
        print("\n## Topic: " + topic + "  (" + str(count) + " entries)\n")
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    e = json.loads(line)
                    val = str(e['value'])[:80]
                    print("  [" + time.strftime("%Y-%m-%d %H:%M", time.localtime(e['ts'])) + "] " + e['key'] + ": " + val)
        return
    print("\n## Memory home: " + str(memory_home()))
    if not idx["topics"]:
        print("  (empty)")
        return
    print("\n  Topic                        Entries  Last updated")
    print("  " + "-" * 60)
    for topic_name, info in sorted(idx["topics"].items()):
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(info.get("last_ts", 0))) if info.get("last_ts") else "?"
        print("  " + topic_name.ljust(28) + " " + str(info.get("count", 0)).rjust(7) + "  " + ts)

def show_context(last_n=10):
    idx = load_index()
    if not idx["topics"]:
        print("[memory] No memory yet. Use: memory.py put --topic=X --key=Y --value=Z")
        return
    print("\n## Recent context (last " + str(last_n) + " entries across all topics)\n")
    all_entries = []
    for topic in idx["topics"]:
        p = topic_path(topic)
        if p.exists():
            with open(p, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            e = json.loads(line)
                            e["_topic"] = topic
                            all_entries.append(e)
                        except Exception:
                            pass
    all_entries.sort(key=lambda x: x.get("ts", 0), reverse=True)
    for e in all_entries[:last_n]:
        ts = time.strftime("%Y-%m-%d %H:%M", time.localtime(e.get("ts", 0)))
        v = str(e.get("value"))[:100]
        print("  [" + ts + "] " + e['_topic'] + "/" + e['key'] + ": " + v)
    print("\nTotal: " + str(len(all_entries)) + " entries")

def main():
    p = argparse.ArgumentParser(description="Persistent memory for autonomous agents")
    sub = p.add_subparsers(dest="cmd", required=True)
    put = sub.add_parser("put")
    put.add_argument("--topic", required=True)
    put.add_argument("--key", required=True)
    put.add_argument("--value", required=True)
    g = sub.add_parser("get")
    g.add_argument("--topic", required=True)
    g.add_argument("--key", required=True)
    lst = sub.add_parser("list")
    lst.add_argument("--topic")
    ctx = sub.add_parser("context")
    ctx.add_argument("--last", type=int, default=10)
    args = p.parse_args()

    if args.cmd == "put":
        append_entry(args.topic, args.key, args.value)
    elif args.cmd == "get":
        e = get_entry(args.topic, args.key)
        if e:
            print(json.dumps(e, ensure_ascii=False))
        else:
            print("[memory] no entry for " + args.topic + "/" + args.key, file=sys.stderr)
            sys.exit(1)
    elif args.cmd == "list":
        list_topic(args.topic)
    elif args.cmd == "context":
        show_context(args.last)

if __name__ == "__main__":
    main()
