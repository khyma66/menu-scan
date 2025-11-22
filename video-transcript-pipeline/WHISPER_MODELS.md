# OpenAI Whisper Model Comparison

## Available Models

Whisper offers multiple model sizes, each with different accuracy and speed trade-offs:

### Model Sizes (Smallest to Largest)

1. **`tiny`** (~39M parameters)
   - Fastest, least accurate
   - Telugu support: ⚠️ Poor

2. **`base`** (~74M parameters) - **Currently Used**
   - Balanced speed/accuracy
   - Telugu support: ⚠️ Moderate (script confusion issues)

3. **`small`** (~244M parameters)
   - Better accuracy than base
   - Telugu support: ✅ Good

4. **`medium`** (~769M parameters)
   - High accuracy
   - Telugu support: ✅ Very Good

5. **`large`** (~1550M parameters)
   - Best accuracy
   - Telugu support: ✅ Excellent

6. **`large-v2`** (~1550M parameters)
   - Improved version of large
   - Telugu support: ✅ Excellent

7. **`large-v3`** (~1550M parameters) - **Recommended**
   - Latest and best version
   - Best Telugu script accuracy
   - Telugu support: ✅ Best

## Recommendation for Telugu

### Best Quality (Recommended)
```python
whisper_model="large-v3"  # Best Telugu script accuracy
```

**Pros:**
- Best script detection (reduces Arabic/Urdu confusion)
- Highest accuracy for Telugu
- Better handling of domain-specific vocabulary

**Cons:**
- Slower processing (~10-15 min per 10-min video)
- Higher memory usage (~10 GB RAM)
- Larger download (~3 GB)

### Balanced Quality/Speed
```python
whisper_model="medium"  # Good balance
```

## How to Change

In `run_telugu_pipeline.py`:
```python
pipeline = TeluguTranscriptionPipeline(
    whisper_model="large-v3",  # Change this
    language="te"
)
```

The model downloads automatically on first use (~3 GB for large-v3).


