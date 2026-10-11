
import json
import subprocess


def get_recent_failed_logins(minutes=5):
    """Collect Windows Security Event ID 4625 records."""

    ps_script = r"""
$start = (Get-Date).AddMinutes(-WINDOW_MINUTES)

try {
    $events = @(
        Get-WinEvent -FilterHashtable @{
            LogName   = 'Security'
            Id        = 4625
            StartTime = $start
        } -ErrorAction Stop
    )

    $results = foreach ($event in $events) {
        [xml]$xml = $event.ToXml()
        $data = @{}

        foreach ($item in $xml.Event.EventData.Data) {
            $data[$item.Name] = [string]$item.'#text'
        }

        [PSCustomObject]@{
            timestamp  = $event.TimeCreated.ToString('o')
            source_ip  = $data['IpAddress']
            username   = $data['TargetUserName']
            logon_type = $data['LogonType']
            event_type = 'failed_login'
        }
    }

    ConvertTo-Json -InputObject @($results) -Compress
}
catch {
    if ($_.FullyQualifiedErrorId -like 'NoMatchingEventsFound*') {
        '[]'
    }
    else {
        [Console]::Error.WriteLine($_.Exception.Message)
        exit 1
    }
}
"""

    ps_script = ps_script.replace(
        "WINDOW_MINUTES", str(max(1, int(minutes)))
    )

    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-Command",
                ps_script
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
    except (subprocess.TimeoutExpired, OSError) as error:
        print(f"Windows log query error: {error}")
        return []

    if result.returncode != 0:
        print("PowerShell error:", result.stderr.strip())
        return []

    output = result.stdout.strip()
    if not output:
        return []

    try:
        events = json.loads(output)
    except json.JSONDecodeError:
        print("Could not parse PowerShell output.")
        return []

    if isinstance(events, dict):
        events = [events]

    if not isinstance(events, list):
        return []

    normalized = []

    for event in events:
        if not isinstance(event, dict):
            continue

        ip = str(event.get("source_ip") or "").strip()

        if not ip or ip in ("-", "::", "::1", "127.0.0.1"):
            event["source_ip"] = "Local/Unknown"

        normalized.append(event)

    return normalized


if __name__ == "__main__":
    events = get_recent_failed_logins(minutes=1440)

    print(f"Failed-login events collected: {len(events)}")

    for event in events[:10]:
        print(event)
