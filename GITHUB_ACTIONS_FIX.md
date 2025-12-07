# GitHub Actions Disk Space Fix

## Problem

GitHub Actions was failing with "No space left on device" error because:
- PyTorch with CUDA dependencies is **~3GB+** in size
- GitHub Actions runners have limited disk space (~14GB total)
- The installation was running out of space

## Solution

I've optimized the workflow to use **CPU-only PyTorch** which is much smaller (~200MB vs ~3GB):

### Changes Made

1. **Updated `.github/workflows/pipeline.yml`:**
   - Install CPU-only PyTorch first: `pip install torch --index-url https://download.pytorch.org/whl/cpu`
   - Install transformers separately
   - Install remaining dependencies
   - Clean up pip cache after installation
   - Added disk space monitoring steps
   - Increased timeout to 45 minutes

2. **Updated `requirements.txt`:**
   - Commented out `torch` (installed separately as CPU-only)
   - Kept other dependencies as-is

### Why CPU-Only PyTorch?

- **GitHub Actions runners don't have GPUs** - CUDA dependencies are unnecessary
- **CPU-only version is ~200MB** vs **~3GB** for CUDA version
- **Saves ~2.8GB** of disk space
- **Still works perfectly** for sentiment analysis (NLP models run fine on CPU)

## What to Do

1. **Commit and push the changes:**
   ```bash
   git add .github/workflows/pipeline.yml requirements.txt
   git commit -m "Fix: Use CPU-only PyTorch for GitHub Actions to save disk space"
   git push origin main
   ```

2. **The workflow should now run successfully!**

3. **Monitor the first run:**
   - Go to "Actions" tab
   - Check disk space output in logs
   - Should see much more available space

## Expected Results

- ✅ Installation completes successfully
- ✅ ~2.8GB disk space saved
- ✅ Pipelines run normally
- ✅ Sentiment analysis works (CPU is fine for NLP)

## Performance Note

**CPU-only PyTorch is perfectly fine for this use case:**
- Sentiment analysis models (FinBERT) run well on CPU
- Batch processing is still fast
- No GPU needed for text classification

If you need GPU acceleration later (for larger models or faster processing), consider:
- Using a self-hosted runner with GPU
- Using cloud services (Render, Railway) with GPU support
- Using GitHub Actions with larger runners (paid)

---

**The workflow should now work!** 🎉

