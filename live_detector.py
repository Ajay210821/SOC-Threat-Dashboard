
import streamlit as st

from windows_logs import get_recent_failed_logins
from detector import detect_brute_force


def get_live_security_alerts():
    """Read recent Windows failed logins and detect brute-force activity."""

    events = get_recent_failed_logins(minutes=5)

    alerts = detect_brute_force(
        events,
        threshold=5,
        window_minutes=5
    )

    return events, alerts


st.subheader("Live Windows Security Monitoring")

if st.button("Refresh Windows Security Logs"):
    with st.spinner("Reading Windows Security logs..."):
        try:
            events, alerts = get_live_security_alerts()

            st.metric("Usable Failed-Login Events", len(events))
            st.metric("Brute-Force Alerts", len(alerts))

            if alerts:
                for alert in alerts:
                    st.error(
                        f"{alert['severity']} | "
                        f"{alert['source_ip']} | "
                        f"{alert['description']}"
                    )
            elif events:
                st.success(
                    "No brute-force pattern detected "
                    "in the retrieved events."
                )
            else:
                st.info(
                    "No failed-login events with usable source IPs "
                    "were found in the last 5 minutes."
                )

        except Exception as error:
            st.error(f"Monitoring error: {error}")
