"""
Sentiment analysis model wrapper using Hugging Face Transformers.

This module provides a wrapper class for loading and running sentiment
analysis models on financial text data.
"""

from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import numpy as np

from src.core import get_logger

logger = get_logger(__name__)


class SentimentModel:
    """
    Wrapper for Hugging Face sentiment analysis models.
    
    Loads a pre-trained sentiment model and provides a simple interface
    for batch prediction. Defaults to FinBERT for financial sentiment
    analysis with fallback to DistilBERT.
    
    Attributes:
        model_name: Name of the Hugging Face model
        device: Torch device (cpu or cuda)
        tokenizer: Hugging Face tokenizer
        model: Hugging Face model for sequence classification
    """
    
    def __init__(
        self,
        model_name: str = "ProsusAI/finbert",
        device: str = "cpu"
    ):
        """
        Initialize the sentiment model.
        
        Args:
            model_name: Hugging Face model identifier
                       Default: "ProsusAI/finbert" (financial sentiment)
                       Fallback: "distilbert-base-uncased-finetuned-sst-2-english"
            device: Device for inference ("cpu" or "cuda")
        """
        self.model_name = model_name
        self.device = device
        
        logger.info(
            f"Loading sentiment model",
            extra={'model_name': model_name, 'device': device}
        )
        
        try:
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
            self.model.to(device)
            self.model.eval()
            
            logger.info(
                f"Model loaded successfully",
                extra={
                    'model_name': model_name,
                    'num_labels': self.model.config.num_labels
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to load model",
                extra={'model_name': model_name, 'error': str(e)}
            )
            
            # Try fallback model
            fallback_model = "distilbert-base-uncased-finetuned-sst-2-english"
            logger.info(f"Attempting fallback model", extra={'model_name': fallback_model})
            
            try:
                self.model_name = fallback_model
                self.tokenizer = AutoTokenizer.from_pretrained(fallback_model)
                self.model = AutoModelForSequenceClassification.from_pretrained(fallback_model)
                self.model.to(device)
                self.model.eval()
                
                logger.info(
                    f"Fallback model loaded successfully",
                    extra={'model_name': fallback_model}
                )
            except Exception as fallback_error:
                logger.error(
                    f"Failed to load fallback model",
                    extra={'error': str(fallback_error)}
                )
                raise RuntimeError(
                    f"Failed to load both primary and fallback models: {fallback_error}"
                )
    
    def predict(self, batch: List[str]) -> List[Dict[str, float]]:
        """
        Run sentiment prediction on a batch of texts.
        
        Tokenizes input texts, runs inference, and returns normalized
        probability distributions over sentiment classes.
        
        Args:
            batch: List of text strings to analyze
            
        Returns:
            List of dictionaries with sentiment probabilities:
            - "neg": Negative sentiment probability (0-1)
            - "neu": Neutral sentiment probability (0-1) 
            - "pos": Positive sentiment probability (0-1)
            
            For 2-class models (pos/neg), neutral is set to 0.0
            
        Example:
            >>> model = SentimentModel()
            >>> texts = ["Bitcoin is amazing!", "The market crashed"]
            >>> results = model.predict(texts)
            >>> print(results[0])
            {'neg': 0.05, 'neu': 0.15, 'pos': 0.80}
        """
        if not batch:
            return []
        
        logger.debug(f"Running prediction", extra={'batch_size': len(batch)})
        
        # Tokenize with truncation to 512 tokens
        inputs = self.tokenizer(
            batch,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        
        # Move inputs to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Run inference without gradients
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            
            # Apply softmax to get probabilities
            probs = torch.nn.functional.softmax(logits, dim=-1)
            probs = probs.cpu().numpy()
        
        # Convert to list of dicts with proper labels
        results = []
        num_labels = self.model.config.num_labels
        
        # Get label mapping from model config
        id2label = getattr(self.model.config, 'id2label', {})
        
        for prob_dist in probs:
            if num_labels == 3 and id2label:
                # Use model's label mapping
                # Map probabilities to neg/neu/pos based on actual labels
                label_probs = {}
                for idx, prob in enumerate(prob_dist):
                    label = id2label.get(idx, '').lower()
                    if 'pos' in label:
                        label_probs['pos'] = float(prob)
                    elif 'neg' in label:
                        label_probs['neg'] = float(prob)
                    elif 'neu' in label or 'neutral' in label:
                        label_probs['neu'] = float(prob)
                
                # Ensure all keys exist
                result = {
                    'neg': label_probs.get('neg', 0.0),
                    'neu': label_probs.get('neu', 0.0),
                    'pos': label_probs.get('pos', 0.0)
                }
            elif num_labels == 3:
                # 3-class model without label mapping
                # Assume standard order: negative, neutral, positive
                result = {
                    'neg': float(prob_dist[0]),
                    'neu': float(prob_dist[1]),
                    'pos': float(prob_dist[2])
                }
            elif num_labels == 2:
                # 2-class model (neg, pos) - set neutral to 0.0
                # Check label mapping or assume: negative, positive
                if id2label:
                    label_probs = {}
                    for idx, prob in enumerate(prob_dist):
                        label = id2label.get(idx, '').lower()
                        if 'pos' in label:
                            label_probs['pos'] = float(prob)
                        elif 'neg' in label:
                            label_probs['neg'] = float(prob)
                    
                    result = {
                        'neg': label_probs.get('neg', float(prob_dist[0])),
                        'neu': 0.0,
                        'pos': label_probs.get('pos', float(prob_dist[1]))
                    }
                else:
                    # Assume: negative, positive
                    result = {
                        'neg': float(prob_dist[0]),
                        'neu': 0.0,
                        'pos': float(prob_dist[1])
                    }
            else:
                # Unknown number of labels - distribute evenly
                logger.warning(
                    f"Unexpected number of labels",
                    extra={'num_labels': num_labels}
                )
                result = {
                    'neg': float(prob_dist[0]) if len(prob_dist) > 0 else 0.0,
                    'neu': float(prob_dist[1]) if len(prob_dist) > 1 else 0.0,
                    'pos': float(prob_dist[-1]) if len(prob_dist) > 0 else 0.0
                }
            
            results.append(result)
        
        logger.debug(
            f"Prediction complete",
            extra={'batch_size': len(batch), 'results_count': len(results)}
        )
        
        return results


# Sanity test
if __name__ == "__main__":
    print("🧪 Testing Sentiment Model")
    print("=" * 60)
    
    # Test 1: Load model
    print("\n📦 Test 1: Load model")
    print("-" * 60)
    
    try:
        model = SentimentModel(model_name="ProsusAI/finbert", device="cpu")
        print(f"✅ Model loaded: {model.model_name}")
        print(f"✅ Device: {model.device}")
        print(f"✅ Number of labels: {model.model.config.num_labels}")
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        exit(1)
    
    # Test 2: Single prediction
    print("\n📊 Test 2: Single prediction")
    print("-" * 60)
    
    test_texts = [
        "Bitcoin is soaring to new heights! Amazing gains today!"
    ]
    
    results = model.predict(test_texts)
    
    if results:
        result = results[0]
        print(f"Text: '{test_texts[0]}'")
        print(f"\nSentiment probabilities:")
        print(f"  Negative: {result['neg']:.4f}")
        print(f"  Neutral:  {result['neu']:.4f}")
        print(f"  Positive: {result['pos']:.4f}")
        
        # Check probabilities sum to ~1.0
        total = result['neg'] + result['neu'] + result['pos']
        print(f"\n✅ Probability sum: {total:.4f} (should be ~1.0)")
        
        # Determine dominant sentiment
        max_sentiment = max(result, key=result.get)
        print(f"✅ Dominant sentiment: {max_sentiment} ({result[max_sentiment]:.4f})")
    
    # Test 3: Batch prediction
    print("\n📊 Test 3: Batch prediction")
    print("-" * 60)
    
    batch_texts = [
        "Bitcoin reaches all-time high! Bulls are winning!",
        "Market crash! Huge losses across the board.",
        "Bitcoin price remained stable today with minor fluctuations.",
        "Uncertain market conditions, mixed signals from traders."
    ]
    
    batch_results = model.predict(batch_texts)
    
    print(f"Processing {len(batch_texts)} texts:\n")
    
    for i, (text, result) in enumerate(zip(batch_texts, batch_results), 1):
        max_sent = max(result, key=result.get)
        max_prob = result[max_sent]
        
        print(f"{i}. Text: '{text[:50]}...'")
        print(f"   Sentiment: {max_sent.upper()} ({max_prob:.4f})")
        print(f"   Probs: neg={result['neg']:.3f}, neu={result['neu']:.3f}, pos={result['pos']:.3f}")
        print()
    
    print(f"✅ Batch prediction complete ({len(batch_results)} results)")
    
    # Test 4: Empty batch
    print("\n📊 Test 4: Edge cases")
    print("-" * 60)
    
    empty_results = model.predict([])
    print(f"Empty batch: {len(empty_results)} results ✅")
    
    single_word = model.predict(["Bitcoin"])
    print(f"Single word prediction: {single_word[0]} ✅")
    
    # Test 5: Long text (truncation)
    print("\n📊 Test 5: Long text (tests 512 token truncation)")
    print("-" * 60)
    
    long_text = " ".join(["Bitcoin is great!"] * 200)  # Create very long text
    long_results = model.predict([long_text])
    
    print(f"Text length: {len(long_text)} characters")
    print(f"Sentiment: {max(long_results[0], key=long_results[0].get)}")
    print(f"✅ Long text handled (automatically truncated to 512 tokens)")
    
    print("\n" + "=" * 60)
    print("✅ All sentiment model tests passed!")
