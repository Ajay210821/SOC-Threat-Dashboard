# SOC Threat Dashboard

A Python + Streamlit Security Operations Center dashboard that reads Windows failed-logon events (Event ID 4625) and detects brute-force login behaviour.

## Features
- Demo Mode (simulated data) and Windows Live Logs mode
- Brute-force detection rule BF-001 (failed logins grouped by source IP)
- Alert severity chart, event timeline, incident table, event explorer

## Run
pip install -r requirements.txt
python -m streamlit run app.py

Windows Live Logs mode needs PowerShell run as Administrator.

## Note
Educational project. Demo Mode data is simulated. The dashboard is a snapshot view (refresh to reload), not continuous monitoring.
