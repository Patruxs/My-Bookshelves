# 🚀 Deploy My Bookshelves to GitHub Pages

## Step 1: Create a GitHub Repository

```bash
# Initialize Git (if not already done)
cd My-Bookshelves
git init
git add .
git commit -m "🎉 Initial commit: My Bookshelves"

# Create repo on GitHub and push
gh repo create My-Bookshelves --public --push
# OR manually create on github.com, then:
git remote add origin https://github.com/YOUR_USERNAME/My-Bookshelves.git
git branch -M main
git push -u origin main
```

## Step 2: Enable GitHub Pages

1. Go to your repo on GitHub → **Settings** → **Pages**
2. Under **Build and deployment**:
   - **Source**: Select **"GitHub Actions"**
3. Done! The workflow will handle the rest automatically.

## Step 3: Push and Deploy

Every time you push to the `main` branch, the GitHub Action will:

1. ✅ Install Python dependencies
2. ✅ Run `generate_data.py` to extract book covers and build `data.json`
3. ✅ Deploy `index.html`, `app.js`, `data.json`, and `assets/` to GitHub Pages

```bash
# After adding new books, just:
git add .
git commit -m "📚 Added new books"
git push
```

## Step 4: Access Your Library

Your library will be live at:

```
https://YOUR_USERNAME.github.io/My-Bookshelves/
```

---

> **⚠️ Note about large files:** GitHub has a 100MB file size limit. If your books exceed this, consider using [Git LFS](https://git-lfs.github.com/) or hosting books elsewhere and updating `file_path` in `data.json` to point to external URLs.

> **💡 Tip:** Add `.env` to your `.gitignore` to avoid accidentally pushing API keys!
