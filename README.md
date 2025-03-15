# Aptos Blockchain Monitor

A modern, real-time monitoring system for the Aptos blockchain with Discord integration and AI-powered event analysis.

![Aptos Blockchain Monitor](https://aptoslabs.com/images/aptos-meta-image.jpg)

## Features

- **Real-time Blockchain Monitoring**: Track events on the Aptos blockchain as they happen
- **Discord Integration**: Receive notifications and interact with the monitor via Discord
- **AI-Powered Analysis**: Intelligent event categorization and summarization
- **Modern UI**: Sleek dark mode interface with responsive design
- **Customizable Alerts**: Set up alerts for specific event types or accounts
- **Event Filtering**: Filter events by type, account, and time range
- **Meme Generation**: Automatic meme generation for significant blockchain events

## Prerequisites

- Python 3.8+
- Discord Bot Token
- Aptos Node Access
- OpenAI API Key (for AI features)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/sivaratrisrinivas/hackathons/cultivate.git
   cd cultivate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Create a `.env` file based on the provided example:
   ```bash
   cp .env.example .env
   ```

4. Update the `.env` file with your configuration details:
   ```
   # Aptos Configuration
   APTOS_NODE_URL=https://fullnode.mainnet.aptoslabs.com/v1
   APTOS_WEBSOCKET_URL=wss://fullnode.mainnet.aptoslabs.com/v1/websocket
   
   # Discord Configuration
   DISCORD_TOKEN=your_discord_token
   DISCORD_CHANNEL_ID=your_channel_id
   DISCORD_PREFIX=!
   
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key
   
   # Web Server Configuration
   WEB_SERVER_HOST=0.0.0.0
   WEB_SERVER_PORT=8000
   ```

## Usage

1. Start the application:
   ```bash
   python main.py
   ```

2. Access the web dashboard:
   ```
   http://localhost:8000
   ```

3. Interact with the Discord bot using commands:
   - `/monitor start` - Start monitoring
   - `/monitor stop` - Stop monitoring
   - `/status` - Check monitoring status
   - `/events [type] [account] [limit]` - View recent events
   - `/alert add [type] [account]` - Set up alerts
   - `/alert list` - View alert configurations
   - `/alert remove [id]` - Remove an alert
   - `/help` - Display help message

## Project Structure

```
cultivate/
├── api/                    # Web API and frontend
│   ├── static/             # Static assets (HTML, CSS, JS)
│   ├── app.py              # Flask application
│   └── routes.py           # API routes
├── modules/                # Core modules
│   ├── ai_module.py        # AI integration
│   ├── blockchain_monitor.py # Blockchain monitoring
│   └── discord_bot.py      # Discord bot integration
├── utils/                  # Utility functions
│   ├── config.py           # Configuration management
│   └── logger.py           # Logging setup
├── .env.example            # Environment variables example
├── main.py                 # Application entry point
└── requirements.txt        # Python dependencies
```

## Deployment

The application can be deployed to cloud platforms like:

- **Heroku**: Easy deployment with Procfile
- **AWS**: Deploy using EC2 or ECS
- **Google Cloud**: Deploy using App Engine or Cloud Run
- **Digital Ocean**: Deploy using Droplets or App Platform

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Contact

For questions or support, please open an issue or contact the repository owner.
