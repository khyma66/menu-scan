# Push to GitHub - Step by Step

## Option 1: Using GitHub CLI (if installed)

```bash
# Create and push in one command
gh repo create menu-ocr --public --source=. --remote=origin --push
```

## Option 2: Manual Setup

### Step 1: Create Repository on GitHub

1. Go to https://github.com/new
2. Repository name: `menu-ocr`
3. Description: "Menu OCR with health-based filtering and Google authentication"
4. Choose Public or Private
5. **DO NOT** check "Initialize with README"
6. Click "Create repository"

### Step 2: Add Remote and Push

Copy the commands GitHub shows you (they'll look like this):

```bash
# Add remote (replace YOUR-USERNAME)
git remote add origin https://github.com/YOUR-USERNAME/menu-ocr.git

# Push to GitHub
git push -u origin main
```

### Step 3: Verify

```bash
git remote -v  # Should show your remote
git log --oneline -1  # Check your commit is there
```

## Option 3: I can help you set it up

If you tell me your GitHub username, I can generate the exact commands for you!

## After Pushing

Once pushed:
- ✅ Code is backed up on GitHub
- ✅ Can deploy directly from GitHub to Render/Vercel
- ✅ Can share with team members
- ✅ Enable GitHub Actions for CI/CD

