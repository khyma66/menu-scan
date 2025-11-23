# Whisper Model Storage Requirements

## Model File Sizes

### Download Sizes (Compressed)
- **`tiny`**: ~75 MB
- **`base`**: ~142 MB  
- **`small`**: ~466 MB
- **`medium`**: ~1.5 GB
- **`large`**: ~3.0 GB
- **`large-v2`**: ~3.0 GB
- **`large-v3`**: ~3.0 GB

### Disk Space After Extraction
Models are stored in `~/.cache/whisper/` directory:

- **`tiny`**: ~75 MB
- **`base`**: ~142 MB
- **`small`**: ~466 MB
- **`medium`**: ~1.5 GB
- **`large`**: ~3.0 GB
- **`large-v2`**: ~3.0 GB
- **`large-v3`**: ~3.0 GB

## Storage Location

All models are cached in:
```
~/.cache/whisper/
```

Example files:
- `tiny.pt` - ~75 MB
- `base.pt` - ~142 MB
- `small.pt` - ~466 MB
- `medium.pt` - ~1.5 GB
- `large-v3.pt` - ~3.0 GB

## Total Storage Needed

### Single Model
- **Minimum** (tiny): ~75 MB
- **Recommended** (large-v3): ~3 GB

### Multiple Models
If you download multiple models, they accumulate:
- `base` + `medium` + `large-v3` = ~4.6 GB
- All models = ~8.5 GB

## Check Current Usage

```bash
# Check Whisper cache size
du -sh ~/.cache/whisper

# List all downloaded models
ls -lh ~/.cache/whisper/*.pt

# Check disk space
df -h ~/.cache/whisper
```

## Cleanup

To free up space, delete unused models:

```bash
# Remove specific model
rm ~/.cache/whisper/base.pt

# Remove all models (will re-download when needed)
rm ~/.cache/whisper/*.pt
```

## Recommendations

### For Development
- Use `base` (~142 MB) for testing
- Upgrade to `large-v3` (~3 GB) for production

### For Production
- Use `large-v3` (~3 GB) - best quality
- Keep only one model to save space

### Storage Tips
1. **Download once**: Models are cached, won't re-download
2. **Delete unused**: Remove models you don't use
3. **Monitor space**: Check `~/.cache/whisper/` regularly
4. **Move cache**: Can change cache location if needed

## Changing Cache Location

```python
import os
os.environ['WHISPER_CACHE_DIR'] = '/path/to/custom/cache'
```

## Current Project Usage

For Telugu transcription pipeline:
- **Recommended**: `large-v3` (~3 GB)
- **Alternative**: `medium` (~1.5 GB) for faster processing

Total storage needed: **~3 GB** (for large-v3)



