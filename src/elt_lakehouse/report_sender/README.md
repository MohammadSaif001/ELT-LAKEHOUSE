# Pipeline report sender

This package builds and optionally emails a summary of pipeline activity.

- `log_parsing.py` reads structured patterns from `logs/application.log`.
- `report_render.py` formats the pipeline summary.
- `email_sender.py` sends the report.
- `email_configure.py` contains email configuration helpers.

Reports are optional. Use `--send-report` with a data action after configuring
`EMAIL_ADDRESS`, `EMAIL_PASSWORD`, and `RECIPIENT_EMAIL`. Do not commit email
credentials or generated report content.
