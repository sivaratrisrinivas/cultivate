#!/usr/bin/env python3
# test_ai.py
import os
import sys
from config import Config
from modules.blockchain import BlockchainEvent
from modules.ai import AIModule
from utils.logger import get_logger

# Set up logging
logger = get_logger("test_ai")

def test_post_generation():
    """Test the AI module's ability to generate posts from blockchain events."""
    logger.info("Testing post generation")
    
    # Load configuration
    config = Config()
    
    # Initialize AI module
    ai_module = AIModule(config)
    
    # Create test events
    test_events = [
        BlockchainEvent(
            "nft_collection_created", 
            {
                "collection_name": "Aptos Monkeys",
                "creator": "0x12345",
                "description": "A collection of 10,000 unique monkey NFTs on Aptos blockchain"
            }, 
            0.9
        ),
        BlockchainEvent(
            "token_event", 
            {
                "amount": "50000",
                "token_name": "APT",
                "sender": "0x67890",
                "receiver": "0xabcde",
                "event_subtype": "large_transfer"
            }, 
            0.85
        ),
        BlockchainEvent(
            "contract_event", 
            {
                "address": "0x54321",
                "module_name": "marketplace",
                "event_subtype": "contract_deployed"
            }, 
            0.8
        )
    ]
    
    # Generate posts for each event
    success = True
    for i, event in enumerate(test_events):
        logger.info(f"Generating post for event {i+1}: {event.event_type}")
        
        try:
            post = ai_module.generate_post(event)
            
            logger.info(f"Generated post: {post['content']}")
            
            if not post or not post.get('content'):
                logger.error("Failed to generate post content")
                success = False
        except Exception as e:
            logger.error(f"Error generating post: {str(e)}")
            success = False
    
    return success

def test_meme_generation():
    """Test the AI module's ability to generate memes from blockchain events."""
    logger.info("Testing meme generation")
    
    # Load configuration
    config = Config()
    
    # Initialize AI module
    ai_module = AIModule(config)
    
    # Create test event
    test_event = BlockchainEvent(
        "nft_collection_created", 
        {
            "collection_name": "Aptos Monkeys",
            "creator": "0x12345",
            "description": "A collection of 10,000 unique monkey NFTs on Aptos blockchain"
        }, 
        0.9
    )
    
    try:
        # Generate meme
        meme = ai_module.generate_meme(test_event)
        
        logger.info(f"Generated meme text: {meme['text']}")
        logger.info(f"Meme image path: {meme['image_path']}")
        
        # Check if meme image was created
        if not os.path.exists(meme['image_path']):
            logger.error(f"Meme image was not created at {meme['image_path']}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error generating meme: {str(e)}")
        return False

def test_question_answering():
    """Test the AI module's ability to answer questions about Aptos."""
    logger.info("Testing question answering")
    
    # Load configuration
    config = Config()
    
    # Initialize AI module
    ai_module = AIModule(config)
    
    # Test questions
    test_questions = [
        "What is Aptos blockchain?",
        "How do I create a wallet on Aptos?",
        "What programming language is used for Aptos smart contracts?",
        "What are the gas fees like on Aptos?"
    ]
    
    # Answer each question
    success = True
    for i, question in enumerate(test_questions):
        logger.info(f"Answering question {i+1}: {question}")
        
        try:
            answer = ai_module.get_answer(question)
            
            logger.info(f"Answer: {answer['answer']}")
            logger.info(f"Confidence: {answer['confidence']}")
            
            if not answer or not answer.get('answer') or answer.get('confidence', 0) < 0.5:
                logger.error("Failed to generate a confident answer")
                success = False
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            success = False
    
    return success

def main():
    """Run all tests."""
    # Create necessary directories
    os.makedirs('data', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('cache/memes', exist_ok=True)
    os.makedirs('templates/memes', exist_ok=True)
    
    # Test post generation
    post_success = test_post_generation()
    
    # Test meme generation
    meme_success = test_meme_generation()
    
    # Test question answering
    qa_success = test_question_answering()
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Post Generation Test: {'PASSED' if post_success else 'FAILED'}")
    logger.info(f"Meme Generation Test: {'PASSED' if meme_success else 'FAILED'}")
    logger.info(f"Question Answering Test: {'PASSED' if qa_success else 'FAILED'}")
    
    if post_success and meme_success and qa_success:
        logger.info("All tests PASSED!")
        return 0
    else:
        logger.error("Some tests FAILED!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)
