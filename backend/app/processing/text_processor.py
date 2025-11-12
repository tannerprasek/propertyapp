"""Text processing utilities for transcript cleaning and normalization."""

import re
import logging
from typing import List, Tuple
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class TranscriptProcessor:
    """Process and clean transcript text."""

    # Common non-content text in transcripts
    BOILERPLATE_PATTERNS = [
        r"forward-looking statements?",
        r"safe harbor",
        r"disclaimer",
        r"copyright.*?all rights reserved",
        r"©.*?\d{4}",
        r"operator|operator speaking",
    ]

    # Speaker identification patterns
    SPEAKER_PATTERNS = [
        r"^[A-Z\s\.]+:\s",  # "NAME:" format
        r"^[A-Z][a-z]+\s+[A-Z][a-z]+\s+[-–]\s",  # "First Last -"
    ]

    def __init__(self):
        """Initialize processor."""
        self.stop_words = set(stopwords.words('english'))

    def clean_transcript(self, text: str) -> str:
        """
        Clean and normalize transcript text.

        Args:
            text: Raw transcript text

        Returns:
            Cleaned transcript text.
        """
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove boilerplate sections
        for pattern in self.BOILERPLATE_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)

        # Remove special characters but keep basic punctuation
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

        # Remove extra dashes and hyphens
        text = re.sub(r'[-–—]+', '-', text)

        return text.strip()

    def extract_speakers(self, text: str) -> List[str]:
        """Extract speaker names from transcript."""
        speakers = set()

        for pattern in self.SPEAKER_PATTERNS:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                speaker = match.rstrip(': -–')
                if len(speaker) > 0 and len(speaker.split()) <= 3:
                    speakers.add(speaker)

        return list(speakers)

    def tokenize_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        try:
            return sent_tokenize(text)
        except Exception as e:
            logger.error(f"Error tokenizing sentences: {e}")
            # Fallback to simple period-based splitting
            return [s.strip() for s in text.split('.') if s.strip()]

    def tokenize_words(self, text: str) -> List[str]:
        """Tokenize text into words."""
        try:
            tokens = word_tokenize(text.lower())
            # Remove stopwords and non-alphanumeric tokens
            return [t for t in tokens if t.isalnum() and t not in self.stop_words]
        except Exception as e:
            logger.error(f"Error tokenizing words: {e}")
            return text.lower().split()

    def extract_context(self, text: str, keyword: str, context_window: int = 100) -> List[Tuple[str, int, int]]:
        """
        Extract sentences containing keyword with surrounding context.

        Args:
            text: Full transcript text
            keyword: Keyword to search for
            context_window: Number of characters before/after to include

        Returns:
            List of (context, start_pos, end_pos) tuples.
        """
        contexts = []

        # Find all occurrences
        pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)

        for match in pattern.finditer(text):
            start = max(0, match.start() - context_window)
            end = min(len(text), match.end() + context_window)

            context = text[start:end]

            # Add ellipsis if truncated
            if start > 0:
                context = "... " + context
            if end < len(text):
                context = context + " ..."

            contexts.append((context, match.start(), match.end()))

        return contexts

    def is_high_quality(self, text: str) -> bool:
        """Check if text appears to be a legitimate transcript."""
        # Basic heuristics
        word_count = len(text.split())
        sentence_count = len(self.tokenize_sentences(text))

        # Should have reasonable length and structure
        if word_count < 500:  # Too short to be a transcript
            return False

        if sentence_count == 0:  # No sentences detected
            return False

        if word_count / max(sentence_count, 1) < 5:  # Average sentence too short
            return False

        return True

def process_transcript(raw_text: str) -> Tuple[str, List[str]]:
    """
    Process a raw transcript.

    Returns:
        Tuple of (cleaned_text, speakers)
    """
    processor = TranscriptProcessor()

    if not processor.is_high_quality(raw_text):
        logger.warning("Transcript quality check failed")

    cleaned = processor.clean_transcript(raw_text)
    speakers = processor.extract_speakers(raw_text)

    return cleaned, speakers
