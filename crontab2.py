#!/usr/bin/env python3
"""crontab2 - Crontab viewer, exporter, and linter.

Single-file, zero-dependency CLI.
"""

import sys
import argparse
import subprocess
import re


def get_crontab():
    try:
        return subprocess.check_output(["crontab", "-l"], text=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return ""


def parse_entry(line):
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    parts = line.split(None, 5)
    if len(parts) < 6:
        return None
    return {"minute": parts[0], "hour": parts[1], "dom": parts[2],
            "month": parts[3], "dow": parts[4], "command": parts[5],
            "raw": line}


def describe_schedule(entry):
    m, h, dom, mon, dow = entry["minute"], entry["hour"], entry["dom"], entry["month"], entry["dow"]
    parts = []
    if m == "*" and h == "*": parts.append("every minute")
    elif m.startswith("*/"):  parts.append(f"every {m[2:]} minutes")
    elif h == "*": parts.append(f"at minute {m} of every hour")
    else:
        parts.append(f"at {h.zfill(2)}:{m.zfill(2)}")
    if dom != "*": parts.append(f"on day {dom}")
    if mon != "*": parts.append(f"in month {mon}")
    if dow != "*":
        days = {"0": "Sun", "1": "Mon", "2": "Tue", "3": "Wed", "4": "Thu", "5": "Fri", "6": "Sat"}
        parts.append(f"on {days.get(dow, dow)}")
    return ", ".join(parts)


def cmd_list(args):
    cron = get_crontab()
    if not cron.strip():
        print("  No crontab entries"); return
    entries = [parse_entry(l) for l in cron.split("\n")]
    entries = [e for e in entries if e]
    for i, e in enumerate(entries, 1):
        desc = describe_schedule(e)
        print(f"  {i:3d}. [{e['minute']:4s} {e['hour']:3s} {e['dom']:3s} {e['month']:3s} {e['dow']:3s}]  {desc}")
        print(f"       → {e['command'][:70]}")


def cmd_lint(args):
    cron = get_crontab()
    if not cron.strip():
        print("  No crontab to lint"); return
    issues = 0
    for i, line in enumerate(cron.split("\n"), 1):
        line = line.strip()
        if not line or line.startswith("#"): continue
        entry = parse_entry(line)
        if not entry:
            print(f"  ⚠️  Line {i}: malformed entry")
            issues += 1
            continue
        if entry["minute"] == "*" and entry["hour"] == "*":
            print(f"  ⚠️  Line {i}: runs every minute — intentional?")
            issues += 1
        if ">" not in entry["command"] and "2>&1" not in entry["command"]:
            print(f"  💡 Line {i}: no output redirection (may generate mail)")
            issues += 1
    if not issues:
        print("  ✅ No issues found")


def cmd_export(args):
    cron = get_crontab()
    if args.output:
        with open(args.output, "w") as f:
            f.write(cron)
        print(f"  Exported to {args.output}")
    else:
        print(cron)


def main():
    p = argparse.ArgumentParser(prog="crontab2", description="Crontab viewer and linter")
    sub = p.add_subparsers(dest="cmd")
    sub.add_parser("list", aliases=["ls"], help="List crontab entries")
    sub.add_parser("lint", help="Lint crontab")
    s = sub.add_parser("export", help="Export crontab")
    s.add_argument("-o", "--output")
    args = p.parse_args()
    if not args.cmd: p.print_help(); return 1
    cmds = {"list": cmd_list, "ls": cmd_list, "lint": cmd_lint, "export": cmd_export}
    return cmds[args.cmd](args) or 0


if __name__ == "__main__":
    sys.exit(main())
