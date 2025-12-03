"""
Text analysis service for content summarization and sentiment detection.

This module provides functions to:
- Generate text summaries
- Detect sentiment (Positive/Negative/Neutral)

Uses HuggingFace API as primary service.
OpenAI API is optional fallback.
"""

import os
import httpx
import re
from typing import Dict, Optional
from dotenv import load_dotenv
from app.models import SentimentType

load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
# HuggingFace Router API endpoint (updated endpoint)
HUGGINGFACE_API_BASE = "https://router.huggingface.co"


async def analyze_with_openai(text: str) -> Dict[str, Optional[str]]:
    """
    Analyze text using OpenAI API.
    
    This function makes an async HTTP request to OpenAI API to:
    1. Generate a summary of the text
    2. Detect sentiment (Positive/Negative/Neutral)
    
    This is an optional fallback if HuggingFace is unavailable.
    
    Args:
        text: The text content to analyze
    
    Returns:
        dict: Contains 'summary' and 'sentiment' keys
    
    Raises:
        Exception: If API call fails
    """
    if not OPENAI_API_KEY:
        raise ValueError("OpenAI API key not configured")
    
    # Prepare the prompt for OpenAI
    prompt = f"""Analyze the following text and provide:
1. A concise summary (2-3 sentences)
2. Sentiment analysis (Positive, Negative, or Neutral)

Text: {text}

Please respond in this format:
Summary: [your summary here]
Sentiment: [Positive/Negative/Neutral]"""
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",  # Using GPT-3.5 for cost efficiency
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 200,
        "temperature": 0.7
    }
    
    # Make async HTTP request
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(OPENAI_API_URL, json=payload, headers=headers)
        response.raise_for_status()  # Raise exception if HTTP error
        
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        # Parse the response
        summary = None
        sentiment = None
        
        # Extract summary and sentiment from response
        lines = content.split("\n")
        for line in lines:
            if line.startswith("Summary:"):
                summary = line.replace("Summary:", "").strip()
            elif line.startswith("Sentiment:"):
                sentiment_str = line.replace("Sentiment:", "").strip()
                # Map to our SentimentType enum
                if "Positive" in sentiment_str:
                    sentiment = SentimentType.POSITIVE
                elif "Negative" in sentiment_str:
                    sentiment = SentimentType.NEGATIVE
                else:
                    sentiment = SentimentType.NEUTRAL
        
        return {
            "summary": summary or "Summary not available",
            "sentiment": sentiment or SentimentType.NEUTRAL
        }


async def analyze_with_huggingface(text: str) -> Dict[str, Optional[str]]:
    """
    Analyze text using HuggingFace API.
    
    Uses separate models for summarization and sentiment analysis.
    
    Args:
        text: The text content to analyze
    
    Returns:
        dict: Contains 'summary' and 'sentiment' keys
    
    Raises:
        Exception: If API call fails
    """
    if not HUGGINGFACE_API_KEY:
        raise ValueError("HuggingFace API key not configured")
    
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:  # Increased timeout for model loading
        # Get summary using summarization model
        # Try multiple reliable models in order
        summary_models = [
            "facebook/bart-large-cnn",  # Best for summarization
            "sshleifer/distilbart-cnn-12-6",  # Faster alternative
        ]
        
        summary = None
        summary_payload = {
            "inputs": text[:512]  # Limit text length for free tier
        }
        
        # Try each model until one works
        for model in summary_models:
            try:
                print(f"Calling HuggingFace summary API: {model}")
                # Router API format: https://router.huggingface.co/models/{model_name}
                summary_response = await client.post(
                    f"{HUGGINGFACE_API_BASE}/models/{model}",
                    json=summary_payload,
                    headers=headers
                )
                
                print(f"HuggingFace summary API status ({model}): {summary_response.status_code}")
                
                if summary_response.status_code == 200:
                    try:
                        summary_data = summary_response.json()
                        print(f"HuggingFace summary response type: {type(summary_data)}")
                        print(f"HuggingFace summary response (first 500 chars): {str(summary_data)[:500]}")
                        
                        # Parse response - handle all formats
                        if isinstance(summary_data, dict):
                            # Check for error first
                            if "error" in summary_data:
                                error_msg = summary_data.get("error", "Unknown error")
                                estimated_time = summary_data.get("estimated_time", 0)
                                print(f"HuggingFace model loading: {error_msg} (estimated time: {estimated_time}s)")
                                continue  # Try next model
                            # New Router Format: {"outputs": [...]}
                            elif "outputs" in summary_data:
                                outputs = summary_data["outputs"]
                                if isinstance(outputs, list) and len(outputs) > 0:
                                    obj = outputs[0]
                                    if isinstance(obj, dict):
                                        summary = obj.get("summary_text") or obj.get("generated_text")
                                    elif isinstance(obj, str):
                                        summary = obj
                            # Direct dict response
                            elif "summary_text" in summary_data:
                                summary = summary_data["summary_text"]
                            elif "generated_text" in summary_data:
                                summary = summary_data["generated_text"]
                        # Old list format
                        elif isinstance(summary_data, list) and len(summary_data) > 0:
                            obj = summary_data[0]
                            if isinstance(obj, dict):
                                summary = obj.get("summary_text") or obj.get("generated_text")
                            elif isinstance(obj, str):
                                summary = obj
                        # Direct string response
                        elif isinstance(summary_data, str):
                            summary = summary_data
                        
                        if summary:
                            print(f"✅ Got summary from {model}: {summary[:100]}...")
                            break  # Success, stop trying other models
                    except Exception as e:
                        print(f"Error parsing HuggingFace summary response ({model}): {e}")
                        continue  # Try next model
                elif summary_response.status_code == 503:
                    # Model is loading - try next model
                    try:
                        error_data = summary_response.json()
                        error_msg = error_data.get("error", "Model unavailable")
                        estimated_time = error_data.get("estimated_time", 0)
                        print(f"HuggingFace model loading ({model}, 503): {error_msg} (estimated time: {estimated_time}s)")
                    except:
                        print(f"HuggingFace model loading ({model}, 503): Model is starting up...")
                    continue  # Try next model
                elif summary_response.status_code == 404:
                    print(f"Model {model} not found (404), trying next model...")
                    continue  # Try next model
                elif summary_response.status_code == 410:
                    # Deprecated endpoint warning - check if response body has data anyway
                    try:
                        response_text = summary_response.text
                        print(f"HuggingFace API deprecated warning ({model}): 410")
                        print(f"Response body preview: {response_text[:300]}")
                        
                        # Try to parse response body - sometimes data is still there
                        try:
                            summary_data = summary_response.json()
                            # Check if it's an error message
                            if isinstance(summary_data, dict) and "error" in summary_data:
                                error_msg = summary_data.get("error", "")
                                print(f"Error message: {error_msg}")
                                # If it's just a deprecation warning, the API might still work
                                # But we need to use router endpoint or different approach
                            else:
                                # Try to extract summary from response
                                if isinstance(summary_data, dict):
                                    if "outputs" in summary_data:
                                        outputs = summary_data["outputs"]
                                        if isinstance(outputs, list) and len(outputs) > 0:
                                            obj = outputs[0]
                                            if isinstance(obj, dict):
                                                summary = obj.get("summary_text") or obj.get("generated_text")
                                            elif isinstance(obj, str):
                                                summary = obj
                                    elif "summary_text" in summary_data:
                                        summary = summary_data["summary_text"]
                                    elif "generated_text" in summary_data:
                                        summary = summary_data["generated_text"]
                                elif isinstance(summary_data, list) and len(summary_data) > 0:
                                    obj = summary_data[0]
                                    if isinstance(obj, dict):
                                        summary = obj.get("summary_text") or obj.get("generated_text")
                                    elif isinstance(obj, str):
                                        summary = obj
                                
                                if summary:
                                    print(f"✅ Got summary from {model} despite 410: {summary[:100]}...")
                                    break
                        except Exception as parse_error:
                            print(f"Could not parse 410 response: {parse_error}")
                    except Exception as e:
                        print(f"Error handling 410 response: {e}")
                    continue  # Try next model
                else:
                    # Other error status
                    try:
                        error_data = summary_response.json()
                        print(f"HuggingFace summary API error ({model}, {summary_response.status_code}): {error_data}")
                    except:
                        print(f"HuggingFace summary API error ({model}, {summary_response.status_code})")
                    continue  # Try next model
            except Exception as e:
                print(f"Exception calling {model}: {e}")
                continue  # Try next model
        
        # Get sentiment using sentiment analysis model
        # Try multiple reliable sentiment models
        sentiment_models = [
            "cardiffnlp/twitter-roberta-base-sentiment-latest",  # Best for social media text
            "distilbert-base-uncased-finetuned-sst-2-english",  # Reliable alternative
        ]
        
        sentiment = SentimentType.NEUTRAL
        sentiment_payload = {"inputs": text[:512]}
        
        # Try each model until one works
        for model in sentiment_models:
            try:
                print(f"Calling HuggingFace sentiment API: {model}")
                # Router API format: https://router.huggingface.co/models/{model_name}
                sentiment_response = await client.post(
                    f"{HUGGINGFACE_API_BASE}/models/{model}",
                    json=sentiment_payload,
                    headers=headers
                )
                
                print(f"HuggingFace sentiment API status ({model}): {sentiment_response.status_code}")
                
                if sentiment_response.status_code == 200:
                    try:
                        sentiment_data = sentiment_response.json()
                        print(f"HuggingFace sentiment response preview: {str(sentiment_data)[:300]}")
                        
                        # Handle new Router format: {"outputs": [[{...}]]}
                        scores_list = None
                        
                        if isinstance(sentiment_data, dict):
                            # New Router Format: {"outputs": [[{...}]]}
                            if "outputs" in sentiment_data:
                                outputs = sentiment_data["outputs"]
                                if isinstance(outputs, list) and len(outputs) > 0:
                                    scores_list = outputs[0]  # First element is the scores list
                        # Old list format: [[{...}]] or [{...}]
                        elif isinstance(sentiment_data, list):
                            if len(sentiment_data) > 0:
                                # Could be [[{...}]] or [{...}]
                                if isinstance(sentiment_data[0], list):
                                    scores_list = sentiment_data[0]
                                else:
                                    scores_list = sentiment_data
                        
                        # Extract sentiment from scores
                        if scores_list and isinstance(scores_list, list) and len(scores_list) > 0:
                            # Find label with highest score
                            max_label = max(scores_list, key=lambda x: x.get("score", 0))
                            label = max_label.get("label", "")
                            score = max_label.get("score", 0)
                            
                            print(f"Detected sentiment label: {label} (confidence: {score:.2f})")
                            
                            # Map HuggingFace labels to our enum
                            label_upper = label.upper()
                            if "POSITIVE" in label_upper or "POS" in label_upper or "LABEL_2" in label_upper or "LABEL_1" in label_upper:
                                sentiment = SentimentType.POSITIVE
                                print(f"✅ Sentiment detected: Positive")
                                break  # Success, stop trying other models
                            elif "NEGATIVE" in label_upper or "NEG" in label_upper or "LABEL_0" in label_upper:
                                sentiment = SentimentType.NEGATIVE
                                print(f"✅ Sentiment detected: Negative")
                                break  # Success, stop trying other models
                            else:
                                sentiment = SentimentType.NEUTRAL
                                # Continue to try next model if this one gave neutral
                    except Exception as e:
                        print(f"Error parsing HuggingFace sentiment response ({model}): {e}")
                        continue  # Try next model
                elif sentiment_response.status_code == 503:
                    print(f"HuggingFace sentiment model loading ({model}, 503)...")
                    continue  # Try next model
                elif sentiment_response.status_code == 404:
                    print(f"Model {model} not found (404), trying next model...")
                    continue  # Try next model
                elif sentiment_response.status_code == 410:
                    # Deprecated endpoint warning - check if response body has data anyway
                    try:
                        response_text = sentiment_response.text
                        print(f"HuggingFace API deprecated warning ({model}): 410")
                        print(f"Response body preview: {response_text[:300]}")
                        
                        # Try to parse response body
                        try:
                            sentiment_data = sentiment_response.json()
                            # Check if it's an error message
                            if isinstance(sentiment_data, dict) and "error" in sentiment_data:
                                error_msg = sentiment_data.get("error", "")
                                print(f"Error message: {error_msg}")
                            else:
                                # Try to extract sentiment from response
                                scores_list = None
                                if isinstance(sentiment_data, dict):
                                    if "outputs" in sentiment_data:
                                        outputs = sentiment_data["outputs"]
                                        if isinstance(outputs, list) and len(outputs) > 0:
                                            scores_list = outputs[0]
                                elif isinstance(sentiment_data, list):
                                    if len(sentiment_data) > 0:
                                        if isinstance(sentiment_data[0], list):
                                            scores_list = sentiment_data[0]
                                        else:
                                            scores_list = sentiment_data
                                
                                if scores_list and isinstance(scores_list, list) and len(scores_list) > 0:
                                    max_label = max(scores_list, key=lambda x: x.get("score", 0))
                                    label = max_label.get("label", "").upper()
                                    score = max_label.get("score", 0)
                                    
                                    print(f"Detected sentiment label: {label} (confidence: {score:.2f})")
                                    
                                    if "POSITIVE" in label or "POS" in label or "LABEL_2" in label or "LABEL_1" in label:
                                        sentiment = SentimentType.POSITIVE
                                        print(f"✅ Sentiment detected: Positive")
                                        break
                                    elif "NEGATIVE" in label or "NEG" in label or "LABEL_0" in label:
                                        sentiment = SentimentType.NEGATIVE
                                        print(f"✅ Sentiment detected: Negative")
                                        break
                        except Exception as parse_error:
                            print(f"Could not parse 410 response: {parse_error}")
                    except Exception as e:
                        print(f"Error handling 410 response: {e}")
                    continue  # Try next model
                else:
                    try:
                        error_data = sentiment_response.json()
                        print(f"HuggingFace sentiment API error ({model}, {sentiment_response.status_code}): {error_data}")
                    except:
                        print(f"HuggingFace sentiment API error ({model}, {sentiment_response.status_code})")
                    continue  # Try next model
            except Exception as e:
                print(f"Exception calling sentiment model {model}: {e}")
                continue  # Try next model
        
        # Fallback: Generate simple summary if AI failed
        if not summary:
            summary = _generate_fallback_summary(text)
            print(f"Using fallback summary generation")
            print(f"Generated fallback summary: {summary[:100] if summary else 'None'}...")
        
        # Ensure summary is not None or empty
        if not summary:
            summary = "Summary not available"
            print("Warning: Fallback summary generation returned empty, using default")
        
        # Fallback: Use keyword-based sentiment if AI failed
        if sentiment == SentimentType.NEUTRAL and summary != "Summary not available":
            sentiment = _detect_sentiment_keywords(text)
            print(f"Using keyword-based sentiment: {sentiment.value}")
        
        print(f"Final result - Summary: {summary[:50] if summary else 'None'}..., Sentiment: {sentiment}")
        
        return {
            "summary": summary,
            "sentiment": sentiment
        }


def _generate_fallback_summary(text: str) -> str:
    """
    Generate a simple summary as fallback when service fails.
    This ensures users always get a summary, even if service is unavailable.
    """
    if not text or not text.strip():
        return "No text provided"
    
    text = text.strip()
    
    # Take first sentence if it's substantial (at least 15 chars)
    sentences = re.split(r'[.!?]+', text)
    if len(sentences) > 0:
        first_sentence = sentences[0].strip()
        if len(first_sentence) > 15:
            # Add punctuation if missing
            if not first_sentence.endswith(('.', '!', '?')):
                first_sentence += "."
            print(f"Fallback: Using first sentence: {first_sentence[:50]}...")
            return first_sentence
    
    # Otherwise take first 30 words
    words = text.split()[:30]
    summary = " ".join(words)
    if len(text.split()) > 30:
        summary += "..."
    
    print(f"Fallback: Using first 30 words: {summary[:50]}...")
    return summary


def _detect_sentiment_keywords(text: str) -> SentimentType:
    """
    Simple keyword-based sentiment detection as fallback.
    Uses word boundary matching to avoid false positives.
    """
    text_lower = text.lower()
    
    # Expanded positive keywords
    positive_words = [
        "love", "loved", "loving", "amazing", "amazed", "great", "excellent", 
        "wonderful", "fantastic", "perfect", "best", "awesome", "outstanding", 
        "good", "happy", "pleased", "delighted", "satisfied", "brilliant", 
        "superb", "marvelous", "incredible", "beautiful", "gorgeous", "stunning",
        "fabulous", "terrific", "magnificent", "exceptional", "remarkable",
        "impressive", "delicious", "tasty", "yummy", "enjoy", "enjoyed", "enjoying"
    ]
    
    # Expanded negative keywords
    negative_words = [
        "hate", "hated", "hating", "terrible", "awful", "bad", "worst", 
        "disappointed", "horrible", "poor", "disgusting", "sad", "angry", 
        "frustrated", "annoyed", "upset", "disgusted", "dreadful", "pathetic",
        "useless", "worthless", "garbage", "trash", "disgusting", "nasty",
        "unhappy", "miserable", "depressed", "furious", "rage", "annoying"
    ]
    
    # Count matches using word boundaries (more accurate)
    import re
    positive_count = 0
    negative_count = 0
    
    for word in positive_words:
        # Use word boundary to match whole words only
        pattern = r'\b' + re.escape(word) + r'\b'
        matches = len(re.findall(pattern, text_lower))
        positive_count += matches
    
    for word in negative_words:
        pattern = r'\b' + re.escape(word) + r'\b'
        matches = len(re.findall(pattern, text_lower))
        negative_count += matches
    
    print(f"Keyword sentiment detection: {positive_count} positive, {negative_count} negative")
    
    if positive_count > negative_count:
        return SentimentType.POSITIVE
    elif negative_count > positive_count:
        return SentimentType.NEGATIVE
    else:
        return SentimentType.NEUTRAL


async def analyze_text(text: str) -> Dict[str, Optional[str]]:
    """
    Main function to analyze text.
    
    Uses HuggingFace API as primary service.
    Falls back to OpenAI if HuggingFace fails.
    
    Args:
        text: The text content to analyze
    
    Returns:
        dict: Contains 'summary' and 'sentiment' keys
    
    Raises:
        Exception: If all AI services fail
    """
    # Check if HuggingFace API key is configured
    huggingface_configured = (
        HUGGINGFACE_API_KEY and 
        HUGGINGFACE_API_KEY.strip() != ""
    )
    
    # Try HuggingFace first (FREE tier)
    if huggingface_configured:
        try:
            print(f"Attempting HuggingFace API analysis...")
            result = await analyze_with_huggingface(text)
            summary = result.get("summary", "")
            if summary and summary != "Summary not available":
                is_fallback = (
                    len(summary.split()) <= 30 or
                    summary.endswith("...") or
                    summary == text[:len(summary)]
                )
                if not is_fallback:
                    print(f"✅ HuggingFace API succeeded")
                    return result
                else:
                    print(f"⚠️ HuggingFace API unavailable - using fallback")
                    return result
            else:
                print(f"⚠️ HuggingFace API unavailable - using fallback")
                return result
        except ValueError as e:
            # API key not configured error
            print(f"HuggingFace API key error: {e}")
        except Exception as e:
            print(f"HuggingFace API failed: {e}")
            # Continue to fallback if available
    
    # Fallback to OpenAI (optional, requires paid account)
    openai_configured = (
        OPENAI_API_KEY and 
        OPENAI_API_KEY != "your-openai-api-key-here" and
        OPENAI_API_KEY.strip() != ""
    )
    
    if openai_configured:
        try:
            print(f"Attempting OpenAI API fallback...")
            return await analyze_with_openai(text)
        except Exception as e:
            print(f"OpenAI API failed: {e}")
    
    if not huggingface_configured and not openai_configured:
        error_msg = (
            "No API keys configured. "
            "Please set HUGGINGFACE_API_KEY in .env file."
        )
        print(error_msg)
        raise ValueError(error_msg)
    else:
        error_msg = "All services unavailable. Check your API keys and network connection."
        print(error_msg)
        raise Exception(error_msg)

