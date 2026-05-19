# Text Processing Fix for Coqui TTS

## Problem
Coqui TTS was throwing "index out of range" errors when processing long or complex text. This is a known issue with XTTS-v2 when:
- Text is too long (>300 characters)
- Text contains special characters
- Text tokenization produces out-of-range token IDs

## Solution Implemented

### 1. Text Preprocessing
- Clean text: Remove problematic special characters
- Normalize whitespace: Multiple spaces become single space
- Keep only common characters: Letters, numbers, basic punctuation

### 2. Text Chunking
- Split long texts (>300 chars) into smaller chunks
- Split by sentences to maintain natural flow
- Generate audio for each chunk separately
- Concatenate chunks into final audio file

### 3. Error Handling
- If a chunk fails, try with even shorter text
- Fallback to 200-character chunks if needed
- Better error messages for debugging

## How It Works Now

**Short text (<300 chars):**
- Direct generation with cleaned text
- Single audio file output

**Long text (>300 chars):**
- Split into sentence-based chunks
- Generate each chunk separately
- Concatenate into final audio
- Uses your custom voice for all chunks

## Benefits

✅ Handles long responses without errors
✅ Maintains natural speech flow
✅ Uses your custom voice throughout
✅ Better error recovery

## Testing

Try sending messages of different lengths:
- Short: "Hello, how are you?"
- Medium: A paragraph (100-300 chars)
- Long: Multiple paragraphs (>300 chars)

All should work with your custom voice!
