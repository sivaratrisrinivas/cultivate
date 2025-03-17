import json
import random
import time
import requests
from datetime import datetime, timedelta

# Create test events with different timestamps
def create_test_events():
    events = []
    
    # Event types with more realistic blockchain events
    event_types = [
        'large_transaction',
        'token_deposit',
        'token_withdrawal',
        'coin_transfer',
        'nft_sale',
        'liquidity_change',
        'price_movement'
    ]
    
    # Collection names
    collections = ['AptoPunks', 'Aptos Monkeys', 'Aptomingos', 'Bruh Bears']
    
    # Token names
    token_templates = ['{} #{:04d}', '{} Genesis #{:04d}', 'Rare {} #{:04d}']
    
    # Real Aptos accounts
    accounts = [
        '0xf3a6b53b2afd1ab787e19fdcc3e6a9e3e4f22826e6ab14af32990a1a4c145033',  # Aptos Labs
        '0x05a97986a9d031c4567e15b797be516910cfcb4156312482efc6a19c0a30c948',  # Topaz
        '0x8f396e4246b2ba87b51c0739ef5ea4f26480d2284be2e0b8876a7c9c8d08a2d4',  # Souffl3
        '0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92'   # BlueMove
    ]
    
    # Create 10 events with different timestamps
    for i in range(10):
        event_type = random.choice(event_types)
        collection = random.choice(collections)
        token_template = random.choice(token_templates)
        token_name = token_template.format(collection, random.randint(1, 9999))
        account = random.choice(accounts)
        
        # Create timestamp with most recent events having newer timestamps
        minutes_ago = (10 - i) * 5  # 5, 10, 15... minutes ago
        timestamp = (datetime.now() - timedelta(minutes=minutes_ago)).isoformat()
        
        # Create event with more detailed data
        event = {
            "event_category": event_type,
            "account": account,
            "account_url": f"https://explorer.aptoslabs.com/account/{account}?network=mainnet",
            "transaction_url": f"https://explorer.aptoslabs.com/txn/{random.randint(10000000, 99999999)}?network=mainnet",
            "timestamp": timestamp,
            "importance_score": random.random() * 0.8 + 0.2,  # Between 0.2 and 1.0
            "id": f"test-event-{i}",
            "details": {}
        }
        
        # Add event-specific details
        if event_type == 'large_transaction':
            amount = random.uniform(10000, 100000)
            event["description"] = f"Large transaction of {amount:.2f} APT detected"
            event["amount_apt"] = amount
            event["details"] = {
                "transaction_type": "transfer",
                "gas_used": random.randint(500, 2000),
                "transaction_version": random.randint(2000000, 3000000)
            }
            
        elif event_type == 'token_deposit' or event_type == 'token_withdrawal':
            event["token_name"] = token_name
            event["collection_name"] = collection
            event["description"] = f"{event_type.replace('_', ' ').title()}: {token_name}"
            event["details"] = {
                "token_id": f"{random.randint(1, 9999)}",
                "creator": random.choice(accounts),
                "transaction_type": "nft_transfer"
            }
            
        elif event_type == 'coin_transfer':
            amount = random.uniform(0.1, 1000)
            event["amount_apt"] = amount
            event["description"] = f"Coin Transfer: {amount:.2f} APT"
            event["details"] = {
                "sender": account,
                "receiver": random.choice(accounts),
                "gas_used": random.randint(100, 500)
            }
            
        elif event_type == 'nft_sale':
            price = random.uniform(10, 5000)
            event["token_name"] = token_name
            event["collection_name"] = collection
            event["amount_apt"] = price
            event["description"] = f"NFT Sale: {token_name} sold for {price:.2f} APT"
            event["details"] = {
                "marketplace": random.choice(["Topaz", "BlueMove", "Souffl3"]),
                "seller": account,
                "buyer": random.choice(accounts),
                "token_id": f"{random.randint(1, 9999)}"
            }
            
        elif event_type == 'liquidity_change':
            change_pct = random.uniform(-30, 50)
            pool_name = random.choice(["APT/USDC", "APT/USDT", "APT/ETH", "APT/BTC"])
            direction = "added to" if change_pct > 0 else "removed from"
            event["description"] = f"Liquidity {direction} {pool_name} pool ({abs(change_pct):.2f}%)"
            event["details"] = {
                "pool": pool_name,
                "change_percentage": change_pct,
                "dex": random.choice(["Liquidswap", "Pontem", "Econia"]),
                "total_value_locked": random.uniform(100000, 10000000)
            }
            
        elif event_type == 'price_movement':
            change_pct = random.uniform(-15, 20)
            token = random.choice(["APT", "zUSDC", "zUSDT", "zETH", "zBTC"])
            direction = "up" if change_pct > 0 else "down"
            event["description"] = f"{token} price moved {direction} by {abs(change_pct):.2f}% in the last hour"
            event["details"] = {
                "token": token,
                "change_percentage": change_pct,
                "current_price": random.uniform(1, 100) if token != "APT" else random.uniform(5, 15),
                "volume_24h": random.uniform(1000000, 50000000)
            }
            
        events.append(event)
    
    return events

def main():
    # Generate test events
    test_events = create_test_events()
    
    # Print the events
    print(f"Generated {len(test_events)} test events")
    for i, event in enumerate(test_events):
        print(f"Event {i+1}: {event['event_category']} - {event['description']} - {event['timestamp']}")
    
    # Send events to the API
    try:
        response = requests.post(
            'http://localhost:5000/api/test_events',
            json=test_events,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            print("\nEvents successfully added to the blockchain monitor.")
            print("The main application should now display these events in the UI.")
            print(f"API Response: {response.json()}")
        else:
            print(f"\nError adding events: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"\nException when adding events: {str(e)}")

if __name__ == "__main__":
    main() 