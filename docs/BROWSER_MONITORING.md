# Browser Monitoring Feature

## Overview

The browser monitoring feature detects when a user manually closes the headed browser instance and automatically forces the program to exit gracefully. This prevents the program from continuing to run when the browser is no longer available.

## How to Enable

The browser monitoring is **disabled by default** to avoid false positives. To enable it, set the environment variable:

```bash
export ENABLE_BROWSER_MONITORING=true
```

Or add it to your `.env` file:

```
ENABLE_BROWSER_MONITORING=true
```

## How It Works

1. **Background Monitoring**: A background thread monitors browser connectivity every 5 seconds
2. **Failure Detection**: Requires 5 consecutive connection failures before triggering
3. **Graceful Exit**: When browser closure is detected, the program exits gracefully
4. **Signal Handling**: Also responds to Ctrl+C and termination signals

## Features

- **Reliable Detection**: Uses browser contexts to check connectivity (more reliable than page creation)
- **False Positive Prevention**: Requires multiple consecutive failures before triggering
- **Graceful Shutdown**: Attempts graceful exit before force termination
- **Signal Handling**: Responds to keyboard interrupts and system signals
- **Debug Logging**: Provides detailed logging when enabled

## Usage

### Basic Usage

```bash
# Enable monitoring
export ENABLE_BROWSER_MONITORING=true

# Run the program
python main.py
```

### Debug Mode

When monitoring is enabled, you'll see output like:

```
[INFO] Browser monitoring started - program will exit if browser is manually closed
[DEBUG] Monitoring will only trigger after 5 consecutive connection failures
```

### Manual Browser Closure

When you manually close the browser window, you'll see:

```
[WARNING] Browser connection lost after 5 consecutive failures: [error details]
[INFO] Browser was manually closed by user - forcing program exit
[INFO] Attempting graceful shutdown...
```

## Configuration

The monitoring behavior can be customized by modifying the `BrowserMonitor` class in `src/scraper.py`:

- `max_failures`: Number of consecutive failures before triggering (default: 5)
- `check_interval`: Seconds between checks (default: 5)
- `timeout`: Timeout for connection checks

## Troubleshooting

### False Positives

If you experience false positives (program exiting when browser is still open):

1. Increase `max_failures` in the `BrowserMonitor` class
2. Increase `check_interval` to reduce check frequency
3. Check for system resource issues that might affect browser connectivity

### Monitoring Not Working

If monitoring doesn't trigger when browser is closed:

1. Verify `ENABLE_BROWSER_MONITORING=true` is set
2. Check that you're running in debug mode (headed browser)
3. Verify the browser is actually closed (not just minimized)

## Technical Details

The monitoring uses Playwright's browser contexts to check connectivity:

```python
contexts = self.browser.contexts
if contexts:  # Browser is still alive
    consecutive_failures = 0
else:
    consecutive_failures += 1
```

This approach is more reliable than creating new pages or accessing internal browser properties.
