
from datetime import datetime, timedelta


def detect_brute_force(events, threshold=5, window_minutes=5):
    """Detect repeated remote-IP and local login failures."""

    failed_events = []

    for event in events:
        if str(event.get("event_type", "")).lower() != "failed_login":
            continue

        try:
            timestamp = datetime.fromisoformat(event["timestamp"])
        except (KeyError, TypeError, ValueError):
            continue

        failed_events.append({
            "timestamp": timestamp,
            "source_ip": event.get("source_ip", "Unknown"),
            "username": event.get("username", "Unknown"),
            "logon_type": str(event.get("logon_type", ""))
        })

    failed_events.sort(key=lambda event: event["timestamp"])

    alerts = []
    alerted_ips = set()
    alerted_users = set()
    window = timedelta(minutes=window_minutes)

    for event in failed_events:
        ip = event["source_ip"]

        # BF-001: Repeated failures from the same known IP.
        if ip and ip not in ("Unknown", "Local/Unknown", "-"):
            if ip not in alerted_ips:
                start = event["timestamp"]
                end = start + window

                matching = [
                    item for item in failed_events
                    if item["source_ip"] == ip
                    and start <= item["timestamp"] <= end
                ]

                if len(matching) >= threshold:
                    alerts.append({
                        "timestamp": end.isoformat(),
                        "rule_id": "BF-001",
                        "description": (
                            f"Possible brute-force activity: "
                            f"{len(matching)} failed logins from "
                            f"{ip} within {window_minutes} minutes"
                        ),
                        "source_ip": ip,
                        "username": event["username"],
                        "severity": "High",
                        "status": "Open",
                        "event_type": "Brute Force"
                    })
                    alerted_ips.add(ip)

        # BF-002: Repeated local interactive login failures.
        if (
            ip == "Local/Unknown"
            and event["logon_type"] == "2"
        ):
            username = event["username"]

            if username in ("", "Unknown") or username in alerted_users:
                continue

            start = event["timestamp"]
            end = start + window

            matching = [
                item for item in failed_events
                if item["source_ip"] == "Local/Unknown"
                and item["logon_type"] == "2"
                and item["username"] == username
                and start <= item["timestamp"] <= end
            ]

            if len(matching) >= threshold:
                alerts.append({
                    "timestamp": end.isoformat(),
                    "rule_id": "BF-002",
                    "description": (
                        f"Repeated local login failures for "
                        f"user {username}: {len(matching)} attempts "
                        f"within {window_minutes} minutes"
                    ),
                    "source_ip": "Local/Unknown",
                    "username": username,
                    "severity": "High",
                    "status": "Open",
                    "event_type": "Local Login Failures"
                })
                alerted_users.add(username)

    return alerts


if __name__ == "__main__":
    from datetime import datetime, timedelta

    now = datetime.now()

    # Test only: five simulated local failures within two minutes.
    sample_events = [
        {
            "timestamp": (now + timedelta(seconds=i * 20)).isoformat(),
            "source_ip": "Local/Unknown",
            "username": "test_user",
            "logon_type": "2",
            "event_type": "failed_login"
        }
        for i in range(5)
    ]

    for alert in detect_brute_force(sample_events):
        print("ALERT DETECTED")
        print(f"Rule: {alert['rule_id']}")
        print(f"Severity: {alert['severity']}")
        print(f"Description: {alert['description']}")
