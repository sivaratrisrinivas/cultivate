# Cultivate: AI-Driven Social Media Manager for Web3 Communities on Aptos

An AI-powered agent that generates viral content, manages community interactions, and enhances protocol adoption for Web3 projects on the Aptos blockchain by integrating real-time blockchain events with Discord.

## Project Structure

```
cultivate/
├── blockchain/     # Blockchain module for Aptos event monitoring
├── ai/             # AI module for content generation and Q&A
├── social/         # Social media module for Discord integration
├── api_gateway/    # API Gateway for inter-module communication
├── frontend/       # Dashboard for monitoring and control
├── requirements.txt # Project dependencies
└── README.md       # Project documentation
```

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/sivaratrisrinivas/hackathons/cultivate.git
   cd cultivate
   ```

2. **Set up a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory with the following variables:
   ```
   # Aptos Blockchain
   APTOS_NODE_URL=https://fullnode.devnet.aptoslabs.com/v1

   # Discord Bot
   DISCORD_BOT_TOKEN=your_discord_bot_token
   DISCORD_CHANNEL_ID=your_discord_channel_id

   # API Gateway
   API_SECRET_KEY=your_secret_key
   ```

5. **Run the application**
   ```bash
   # Start the API Gateway
   cd api_gateway
   uvicorn main:app --reload
   ```

## Features

- **Content Generation**: Daily AI-generated posts based on notable Aptos blockchain events
- **Interaction Management**: AI responses to frequent Aptos-related questions on Discord
- **Blockchain Integration**: Real-time data retrieval from Aptos blockchain
- **Social Media Integration**: Publishing to Discord with potential expansion to other platforms

## Development

This project is under active development for the Move AI hackathon (deadline: April 23, 2025).

## License

MIT 