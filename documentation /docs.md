# Documentation

## Aptos

[Aptos](https://aptos.dev/en)

# Aptos Blockchain Event Documentation

## Event Handles in Aptos

Events in Aptos are emitted during transaction execution and are stored within event stores within the global state. Each Move module can define its own events and choose when to emit them.

### Core Event Handles

#### Token Events
- **Token Store**: `0x3::token::TokenStore`
  - Deposit events: `deposit_events`
  - Withdraw events: `withdraw_events`
- **Token Collections**: `0x3::token::Collections`
  - Create collection events: `create_collection_events`

#### Coin Events
- **Coin Store**: `0x1::coin::CoinStore<CoinType>`
  - Deposit events: `deposit_events`
  - Withdraw events: `withdraw_events`
- **APT Coin**: `0x1::coin::CoinStore<0x1::aptos_coin::AptosCoin>`

#### Contract Events
- **Package Registry**: `0x1::code::PackageRegistry`
  - Publish package events: `upgrade_events`

#### Governance Events
- **Governance**: `0x1::aptos_governance::GovernanceEvents`
  - Create proposal events: `create_proposal_events`
  - Vote events: `vote_events`

#### Staking Events
- **Stake**: `0x1::stake::StakePool`
  - Add stake events: `add_stake_events`
  - Withdraw stake events: `withdraw_stake_events`
  - Distribution pool events: `distribute_events`

### NFT Marketplace Events (Topaz)
- **Marketplace**: `0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2::marketplace::MarketEvents`
  - Listing events: `listing_events`
  - Sale events: `sale_events`
  - Cancel events: `cancel_events`

### Important Accounts
- **Aptos Foundation**: `0x1`
- **Aptos Labs**: `0x0108bc32f7de18a5f6e1e7d6ee7aff9f5fc858d0d87ac0da94dd8d2a5d267d6b`
- **Binance**: `0xc6b2c2483d1495084a13169f707fbe7271b4a78e4325e8c8d3d6068a354c7a92`
- **Coinbase**: `0x8f396e4246b2ba87b51c0739ef5ea4f26480d2284be2e0b8876a7c9c8d08a2d4`
- **Topaz Marketplace**: `0x2c7bccf7b31baf770fdbcc768d9e9cb3d87805e255355df5db32ac9a669010a2`
- **Aptomingos**: `0x25a125ffc4634e095d9fbd8ec34e0b1cef2c8cd1b66f347bef9f4182b883796c`

### Event Structure
Events in Aptos have the following structure:
```json
{
  "version": "string",
  "guid": {
    "creation_number": "string",
    "account_address": "string"
  },
  "sequence_number": "string",
  "type": "string",
  "data": {}
}
```

### Querying Events
Events can be queried through the REST API:
- By event handle: `/accounts/{address}/events/{event_handle_struct}/{field_name}`
- By creation number: `/accounts/{address}/events/{creation_number}`

### Best Practices
- Filter events by version to avoid processing duplicates
- Use pagination when querying large numbers of events
- Cache processed events to avoid reprocessing
- Handle resource not found errors gracefully








[kivy](https://kivy.org/doc/stable/)