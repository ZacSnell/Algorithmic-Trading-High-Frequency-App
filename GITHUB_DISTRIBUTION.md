# GitHub Deployment & Distribution Guide

## 📦 Setup for Easy GitHub Releases & Distribution

Your ML Trading System can be easily distributed to any Windows machine via GitHub releases. Here's how to set it all up.

---

## Part 1: GitHub Repository Setup

### 1. Update Your Repository

```bash
cd /path/to/Algorithmic-Trading-High-Frequency-App

# Configure if not done yet
git config user.email "your-email@gmail.com"
git config user.name "Your Name"

# Create initial commit
git add .
git commit -m "Initial commit: ML Trading System with GUI"
git branch -M main
git remote add origin https://github.com/YourUsername/Algorithmic-Trading-High-Frequency-App

# Push to GitHub
git push -u origin main
```

### 2. Create `.gitignore` Update

The system already includes a `.gitignore`, but here's what it should contain:
```
# Executables & builds
dist/
build/
*.exe
*.spec
*.msi

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.venv/
venv/

# Secrets
.env
.env.local

# Data files
*.csv
*.json (except config files)

# IDE
.vscode/
.idea/
*.swp
```

---

## Part 2: Building the Executable

### 1. Install Dependencies

```bash
cd services
pip install -r ../requirements.txt
```

### 2. Build Executable

```bash
# From project root
python build_executable.py
```

This creates:
- `dist/MLTradingSystem.exe` - Your standalone application
- `RUN.bat` - Quick launch script

Or with automatic cleanup:
```bash
python build_executable.py --clean
```

### 3. Test the Executable

```bash
# Double-click RUN.bat or run directly
dist\MLTradingSystem.exe
```

**First run will take a moment to extract embedded files.**

---

## Part 3: Publishing to GitHub (Automated)

### Option A: Manual GitHub Release (Easiest)

```bash
# Build executable
python build_executable.py

# Commit the latest code
git add .
git commit -m "v1.0.0: GUI release with auto-updater"
git push origin main

# Go to GitHub → Releases → Create new release
# - Tag: v1.0.0
# - Title: ML Trading System v1.0.0
# - Upload file: dist/MLTradingSystem.exe
# - Publish release
```

### Option B: GitHub Actions (Automated Builds)

Create `.github/workflows/build.yml`:

```yaml
name: Build Executable

on:
  release:
    types: [created]
  workflow_dispatch:

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.14'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Build executable
      run: python build_executable.py
    
    - name: Upload to release
      uses: softprops/action-gh-release@v1
      with:
        files: dist/MLTradingSystem.exe
```

Then push and let GitHub automatically build & attach .exe to releases!

---

## Part 4: Distribution to End Users

### Simple Distribution Steps

**For anyone who wants to use your system:**

1. **Go to GitHub Releases page**
   ```
   https://github.com/YourUsername/Algorithmic-Trading-High-Frequency-App/releases
   ```

2. **Download latest `MLTradingSystem.exe`**

3. **Create `.env` file** with their API keys:
   ```
   ALPACA_API_KEY=their_key_here
   ALPACA_SECRET_KEY=their_secret_here
   PAPER_MODE=True
   ```

4. **Double-click `MLTradingSystem.exe`**

5. **That's it!** System starts trading automatically

---

## Part 5: Auto-Update Feature

The application supports automatic updates from GitHub releases.

### Enable Auto-Update Check

```python
# In trading_gui.py, add to TradingGUI.__init__():
from auto_updater import AutoUpdater

updater = AutoUpdater("YourUsername", "Algorithmic-Trading-High-Frequency-App")
latest = updater.get_latest_release()

if updater.has_update(latest):
    show_dialog("Update available! Download from GitHub releases")
```

### Manual Update Check

```bash
python auto_updater.py --check-only
```

### Auto-Install Update

```bash
python auto_updater.py
```

---

## Part 6: Version Management

### Update Version for Each Release

In `trading_gui.py`:
```python
class TradingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ML Trading System v1.1.0")  # Update this
```

In `auto_updater.py`:
```python
class AutoUpdater:
    def __init__(self, ...):
        self.current_version = "1.1.0"  # Update this
```

### Semantic Versioning
- `MAJOR.MINOR.PATCH`
- `1.0.0` - First release
- `1.1.0` - New feature (auto-updater)
- `1.1.1` - Bug fix
- `2.0.0` - Major overhaul

---

## Part 7: Release Checklist

Before each release:

- [ ] Update version numbers in code
- [ ] Run all tests with `python ml_trainer.py`
- [ ] Test GUI with `python services/trading_gui.py`
- [ ] Build executable: `python build_executable.py`
- [ ] Test standalone executable: `dist/MLTradingSystem.exe`
- [ ] Update `CHANGELOG.md` with new features
- [ ] Commit & push: `git push origin main`
- [ ] Create GitHub release with tag
- [ ] Attach executable to release
- [ ] Add release notes

---

## Part 8: Directory Structure After Build

```
Algorithmic-Trading-High-Frequency-App/
├── dist/
│   └── MLTradingSystem.exe          ← Distribute this!
├── services/
│   ├── trading_gui.py               ← GUI source
│   ├── live_trader.py
│   ├── ml_trainer.py
│   ├── ml_predictor.py
│   ├── config.py
│   ├── .env                         ← Users create this
│   └── models/
│       ├── model_*.pkl
│       └── trade_history.json
├── build_executable.py
├── auto_updater.py
├── requirements.txt
└── README.md
```

---

## Part 9: User Instructions Document

Create `INSTALLATION.md` for end users:

```markdown
# Installation & Setup

## Quick Start

1. **Download** `MLTradingSystem.exe` from GitHub Releases
2. **Create** `config/.env` file with:
   ```
   ALPACA_API_KEY=your_key
   ALPACA_SECRET_KEY=your_secret
   PAPER_MODE=True
   ```
3. **Run** `MLTradingSystem.exe`
4. **Click** "START TRADING"

## First Time Setup

- Download historical data automatically
- Train model automatically (8 PM)
- Start trading next morning (9:30 AM)

## Updating

- Check for updates in Settings tab
- Or download latest from GitHub Releases
- Old version automatically backed up
```

---

## Part 10: GitHub Secrets for CI/CD (Optional)

If using GitHub Actions, store secrets:

1. Go to GitHub repo → Settings → Secrets
2. Add secrets:
   - `PYINSTALLER_FILENAME` (e.g., `MLTradingSystem.exe`)
   - Others if needed

Then reference in workflows:
```yaml
- name: Build
  env:
    FILENAME: ${{ secrets.PYINSTALLER_FILENAME }}
  run: |
    # build command
```

---

## Common Issues & Solutions

### Issue: "dist/ folder is blank"
**Solution:** Run `python build_executable.py` from project root

### Issue: "Executable too large (>200MB)"
**Solution:** Use `--onefile` option (already enabled, combines everything)

### Issue: "Antivirus flags .exe as suspicious"
**Solution:** Common with PyInstaller. Sign executable with certificate (advanced)

### Issue: "Update check fails"
**Solution:** Update repo owner/name in `auto_updater.py`

---

## Distribution Methods

### Method 1: Direct GitHub Release (Best)
- Easy to share link
- Auto-update support
- Version history

### Method 2: Website Download
- Host on your website
- Manual download
- Embed update check

### Method 3: Package Installer
- Create MSI installer
- Windows native feel
- More professional

### Method 4: PortableApps Format
- Zero installation
- Run from USB
- Great for testing

---

## Next Steps

1. **Build:** `python build_executable.py`
2. **Test:** `dist/MLTradingSystem.exe`
3. **Push:** `git push origin main`
4. **Release:** Create GitHub release with .exe
5. **Share:** Send link to users: `https://github.com/YourUsername/repo/releases`

---

## Long-Term Maintenance

### Weekly
- Monitor GitHub issues/feedback
- Fix bugs reported
- Minor updates

### Monthly
- New features
- Performance improvements
- Release new version

### Quarterly
- Major overhaul
- Add new strategies
- Update documentation

---

**Your system is now ready for public release & continuous updates!** 🚀

Share the GitHub link and anyone can download, run, and auto-update your trading system!
