import psutil
import time
from datetime import datetime
from core.memory.behavioral_memory import update_memory, memory_risk_boost

from core.scoring.risk_engine import calculate_risk
from core.defense.defender import block_process
from forensics.timeline import log_event
from gui.dashboard import push_event
from config.loader import load_config


config = load_config()

LOLBINS = config["lolbins"]
RISK_BLOCK_THRESHOLD = config["risk_block_threshold"]
DEFENSE_MODE = config.get("defense_mode", "block")


def watch_processes(stop_flag=None):
    seen = set()

    while True:
        if stop_flag and stop_flag.is_set():
            break

        for proc in psutil.process_iter(["pid", "ppid", "name", "cmdline"]):
            try:
                if proc.pid in seen:
                    continue
                seen.add(proc.pid)

                name = proc.info["name"]
                if not name:
                    continue

                name = name.lower()
                if name not in LOLBINS:
                    continue

                cmdline = proc.info["cmdline"]
                cmd = " ".join(cmdline).lower() if cmdline else ""

                # 🔐 Base risk calculation (Round-2 stable logic)
                risk, reasons = calculate_risk(name, cmd)

                event = {
                    "pid": proc.pid,
                    "ppid": proc.ppid(),
                    "process": name,
                    "command": cmdline,
                    "risk": risk,
                    "reasons": reasons
                }

                # 🎨 GUI color mapping
                msg = (
                    f"[{datetime.now().strftime('%H:%M:%S')}] "
                    f"{name} | Risk={risk} | Reasons={reasons}"
                )

                if risk < 30:
                    push_event("🟢 " + msg, "low")
                elif risk < 60:
                    push_event("🟡 " + msg, "medium")
                else:
                    push_event("🔴 " + msg, "high")

                log_event(event)

                # 🛑 Defense action
                if risk >= RISK_BLOCK_THRESHOLD:
                    if DEFENSE_MODE == "alert":
                        push_event("🚨 HIGH RISK → ALERT ONLY", "blocked")
                    elif DEFENSE_MODE == "block":
                        push_event("🛑 🚨 HIGH RISK → PROCESS BLOCKED", "blocked")
                        block_process(proc.pid)

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        time.sleep(1)
