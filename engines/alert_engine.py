
"""IFIT V0.7.1 — Event Memory & Alert Engine."""

SEVERITY_WEIGHT={"HIGH":100,"MEDIUM":65,"INFO":25,"LOW":25}


def _key(item):
    return f'{item.get("kind","SYSTEM")}::{item.get("title","UNKNOWN")}'


def rank_events(events):
    """Rank event records by severity and event score."""
    ranked=[]
    for e in events:
        x=dict(e)
        sev=x.get("severity","INFO")
        x["priority_score"]=round(
            0.65*SEVERITY_WEIGHT.get(sev,25)+0.35*float(x.get("score",0) or 0),1
        )
        ranked.append(x)
    return sorted(ranked,key=lambda x:x["priority_score"],reverse=True)


def update_memory(memory, new_events, current_flags):
    """Update persistent event memory with NEW/ONGOING/RESOLVED states."""
    memory=memory or {}
    records=memory.get("records",{})
    previous_active=set(memory.get("active_keys",[]))

    incoming={_key(e):e for e in new_events}
    flag_keys=set()
    for sev,condition in current_flags:
        # Current conditions are persistent states; use normalized condition text.
        flag_keys.add(f"FLAG::{condition}")

    # New event detections become active records.
    for key,e in incoming.items():
        rec=dict(e)
        rec["key"]=key
        prior_status=records.get(key,{}).get("status")
        rec["status"]="ONGOING" if prior_status in ("NEW","ONGOING") else "NEW"
        rec["occurrences"]=int(records.get(key,{}).get("occurrences",0))+1
        records[key]=rec

    # Persistent watchlist conditions become active records.
    for sev,condition in current_flags:
        key=f"FLAG::{condition}"
        old=records.get(key,{})
        records[key]={
            "key":key,
            "timestamp":old.get("timestamp","--"),
            "kind":"WATCH",
            "severity":sev,
            "title":condition,
            "detail":"Condition remains active on the current refresh.",
            "score":SEVERITY_WEIGHT.get(sev,25),
            "priority_score":SEVERITY_WEIGHT.get(sev,25),
            "status":"ONGOING" if key in previous_active else "NEW",
            "occurrences":int(old.get("occurrences",0))+1,
        }

    current_active=set(incoming)|flag_keys
    # Mark previously active items absent from the current state as resolved.
    for key in previous_active-current_active:
        if key in records:
            records[key]["status"]="RESOLVED"

    # Active set is the current state; resolved history stays in records.
    memory["records"]=records
    memory["active_keys"]=list(current_active)
    return memory


def alert_snapshot(memory):
    """Return ranked active alerts plus counts and the highest-priority alert."""
    records=list((memory or {}).get("records",{}).values())
    active=[r for r in records if r.get("status") in ("NEW","ONGOING")]
    resolved=[r for r in records if r.get("status")=="RESOLVED"]
    ranked=rank_events(active)
    top=ranked[0] if ranked else None
    counts={
        "new":sum(1 for r in active if r.get("status")=="NEW"),
        "ongoing":sum(1 for r in active if r.get("status")=="ONGOING"),
        "resolved":len(resolved),
        "active":len(active),
    }
    if top:
        summary=f'{top["severity"]} — {top["title"]}'
        if top.get("detail"):
            summary += f' | {top["detail"]}'
    else:
        summary="No high-priority active alert"
    return {"active":ranked,"resolved":sorted(resolved,key=lambda x:x.get("priority_score",0),reverse=True),
            "top":top,"counts":counts,"summary":summary}


def clear_memory():
    return {"records":{}, "active_keys":[]}
