@echo off
REM Run main.py while filtering out GLib-GIO warnings
python main.py 2>nul | findstr /V "GLib-GIO-WARNING"


