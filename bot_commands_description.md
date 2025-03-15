# 🤖 Aptos Blockchain Monitor Bot

Welcome to the **Aptos Blockchain Monitor** command center! This channel is dedicated to interacting with our blockchain monitoring bot.

## 🔍 Available Commands

| Command | Description |
|---------|-------------|
| `/monitor start` | Start monitoring the blockchain for events |
| `/monitor stop` | Stop the monitoring process |
| `/status` | Check the current status of the monitoring system |
| `/events [type] [account] [limit]` | View recent blockchain events with optional filters |
| `/alert add [type] [account]` | Set up alerts for specific event types or accounts |
| `/alert list` | View your current alert configurations |
| `/alert remove [id]` | Remove a specific alert configuration |
| `/help` | Display this help message |

## 🔔 Event Types

- `deposit` - Token deposit events
- `withdraw` - Token withdrawal events
- `trade` - Trading events
- `transfer` - Coin transfer events
- `all` - All event types

## 💡 Examples

```
/events withdraw 5
```
Shows the last 5 withdrawal events

```
/alert add deposit 0x1234...5678
```
Alerts you when deposits occur for the specified account

## 📊 Dashboard

Access the web dashboard for more detailed analytics and visualizations:
[Aptos Blockchain Monitor Dashboard](http://localhost:8000)

---

*For technical support or feature requests, please contact the administrators.*
