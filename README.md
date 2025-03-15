# Cultivate - Aptos Blockchain Social Manager

Cultivate is an AI-powered social media manager for Aptos blockchain communities. It monitors blockchain events, analyzes them using AI, and posts conversational updates to Discord.

## Features

- **Real-time Blockchain Monitoring**: Monitors Aptos blockchain events in real-time
- **AI-Powered Analysis**: Uses AI to generate insights and conversational messages about blockchain events
- **Selective Notifications**: Only sends notifications for events related to monitored accounts, tokens, or collections
- **Discord Integration**: Posts updates to Discord with rich, conversational embeds
- **User Management**: Allows users to manage which accounts, tokens, and collections they want to monitor

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with the required configuration (see `.env.example`)
4. Run the application: `python main.py`

## Configuration

Configure the application by setting the following environment variables in a `.env` file:

```
# Discord Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token
DISCORD_CHANNEL_ID=your_discord_channel_id
DISCORD_PREFIX=!

# AI Configuration
XAI_API_KEY=your_xai_api_key
XAI_API_URL=https://api.x.ai/v1
GROK_MODEL=grok-2-latest
AI_TEMPERATURE=0.7

# Blockchain Configuration
APTOS_NODE_URL=https://fullnode.mainnet.aptoslabs.com/v1
APTOS_NETWORK=mainnet
POLLING_INTERVAL=60

# Monitoring Configuration (comma-separated lists)
MONITOR_ACCOUNTS=0x1,0x2,0x3
MONITOR_TOKENS=TokenName1,TokenName2
MONITOR_COLLECTIONS=CollectionName1,CollectionName2
```

## Discord Commands

The Discord bot supports the following commands:

- `!aptos` - Get information about Aptos blockchain
- `!blockchain_info` - Get information about the blockchain monitor
- `!monitor add|remove|list account|token|collection [value]` - Manage monitored items
- `!bot_help` - Show help message
- `!stats` - View current blockchain statistics
- `!recent` - See recent significant events
- `!campaign` - See active community campaigns
- `!status` - Check the bot status
- `!latest` - Get the latest blockchain events

## Managing Monitored Items

You can manage which accounts, tokens, and collections are monitored using the `!monitor` command:

### List Monitored Items
```
!monitor list
```

### Add Items to Monitor
```
!monitor add account 0x123456789abcdef
!monitor add token MyToken
!monitor add collection MyCollection
```

### Remove Items from Monitoring
```
!monitor remove account 0x123456789abcdef
!monitor remove token MyToken
!monitor remove collection MyCollection
```

## How It Works

1. The application connects to the Aptos blockchain and monitors events
2. When an event is detected, it checks if it's related to any monitored accounts, tokens, or collections
3. If it is, the event is analyzed using AI to generate insights
4. A conversational message is created and posted to Discord
5. Users can interact with the bot to manage monitored items and get information

## Development

- `modules/` - Core application modules
- `api/` - API server
- `utils/` - Utility functions
- `tests/` - Unit tests

## License

MIT
