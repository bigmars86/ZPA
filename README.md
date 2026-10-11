# ZPA (Zoom Poll Analyzer)

[![CI](https://img.shields.io/github/actions/workflow/status/bigmars86/ZPA/ci.yml?branch=main&label=CI&logo=githubactions&logoColor=white)](https://github.com/bigmars86/ZPA/actions/workflows/ci.yml)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/bigmars86/ZPA/codeql.yml?branch=main&label=CodeQL&logo=github)](https://github.com/bigmars86/ZPA/actions/workflows/codeql.yml)
[![Release](https://img.shields.io/github/v/release/bigmars86/ZPA?sort=semver&display_name=tag&logo=github)](https://github.com/bigmars86/ZPA/releases/latest)
[![Downloads](https://img.shields.io/github/downloads/bigmars86/ZPA/total?logo=github)](https://github.com/bigmars86/ZPA/releases)
[![License](https://img.shields.io/github/license/bigmars86/ZPA)](LICENSE)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fbigmars86%2FZPA%2Fmain%2Fpyproject.toml&logo=python&logoColor=white)](pyproject.toml)
[![Platform](https://img.shields.io/badge/platform-Windows-0078D6)](https://github.com/bigmars86/ZPA/releases/latest)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![gitleaks](https://img.shields.io/badge/protected%20by-gitleaks-blue)](https://github.com/gitleaks/gitleaks)
[![Dependabot](https://img.shields.io/badge/Dependabot-enabled-025E8C?logo=dependabot)](.github/dependabot.yml)
[![Last commit](https://img.shields.io/github/last-commit/bigmars86/ZPA)](https://github.com/bigmars86/ZPA/commits/main)

A modern PyQt6 desktop application for analyzing Zoom meeting poll results. ZPA connects to Zoom's API to retrieve poll data from meetings and provides comprehensive analysis and export capabilities.

## Download

Get the latest standalone Windows build - no Python installation required:

**[Download ZPA.exe](https://github.com/bigmars86/ZPA/releases/latest/download/ZPA.exe)** ([all releases](https://github.com/bigmars86/ZPA/releases))

- On first start ZPA creates `zpa.ini` next to the exe. Enter your Zoom API credentials via **File → Settings** (see [Zoom API Credentials Setup](#zoom-api-credentials-setup)).
- The exe is not code-signed, so Windows SmartScreen may warn on first start ("More info" → "Run anyway").
- Every release ships a `ZPA.exe.sha256` checksum and a signed [build provenance attestation](https://docs.github.com/en/actions/security-for-github-actions/using-artifact-attestations). Verify the download with the GitHub CLI:

  ```bash
  gh attestation verify ZPA.exe --repo bigmars86/ZPA
  ```

## Features

- **Multi-language Support**: English, German (Deutsch), and Greek (Ελληνικά)
- **Dynamic Theme System**: Light, Dark, Solarized Light, and Solarized Dark themes with JSON-based customization
- **Zoom API Integration**: Secure OAuth2 server-to-server authentication
- **Data Analysis**: Comprehensive poll result analysis with colored row visualization
- **Multiple Export Formats**: CSV, JSON, YAML, and XML exports with UTF-8 encoding
- **Command Line Support**: CLI arguments for custom INI file paths
- **Configurable Settings**: Persistent INI-based configuration with organized sections
- **Responsive UI**: Auto-resizing tables and optimized column sizing
- **Cross-platform**: Works on Windows, macOS, and Linux

## Requirements

- Python 3.8 or higher
- PyQt6 6.5.0 or higher
- Active Zoom account with API credentials
- Internet connection for API access

## Installation

### Using uv (recommended)

```bash
# Install uv if you haven't already
pip install uv

# Clone the repository
git clone https://github.com/bigmars86/ZPA.git
cd ZPA

# Install dependencies
uv sync

# Run the application
uv run zpa
```

### Using pip

```bash
# Clone the repository
git clone https://github.com/bigmars86/ZPA.git
cd ZPA

# Install in development mode
pip install -e .

# Run the application
zpa
```

### Alternative execution methods

```bash
# Run as module
python -m src.zpa

# Run directly
python src/zpa/main.py
```

## Zoom API Credentials Setup

To use this application, you need to create a Zoom Server-to-Server OAuth app and obtain API credentials. Follow these detailed steps:

### Step 1: Access Zoom Marketplace

1. Open your web browser and go to [Zoom Marketplace](https://marketplace.zoom.us/)
2. Sign in with your Zoom account credentials
3. If you don't have a Zoom account, create one first at [zoom.us](https://zoom.us/)

### Step 2: Create a New App

1. Once logged in, click on **"Develop"** in the top navigation menu
2. Select **"Build App"** from the dropdown menu
3. You'll see different app types - choose **"Server-to-Server OAuth"**
4. Click **"Create"** button

### Step 3: Configure Basic Information

1. **App Name**: Enter a descriptive name (e.g., "Poll Analyzer App")
2. **Company Name**: Enter your company or organization name
3. **Developer Name**: Enter your name
4. **Developer Email**: Enter your email address
5. **App Description**: Enter a brief description of what the app does
6. Click **"Continue"** to proceed

### Step 4: Configure App Information

1. **Short Description**: Provide a concise description
2. **Long Description**: Provide a detailed description of your app's purpose
3. **Developer Information**: Fill in any additional required fields
4. Click **"Continue"** to proceed

### Step 5: Configure Scopes (Permissions)

**Important**: Your app needs specific permissions to access meeting and poll data.

Add the following scopes by clicking **"Add Scopes"**:

**Required Scopes:**
- `meeting:read:admin` - Read meeting information
- `report:read:admin` - Read meeting reports and participant data

**Additional Recommended Scopes:**
- `meeting:read` - Basic meeting read access
- `user:read:admin` - Read user information (if needed)

**How to add scopes:**
1. Click **"+ Add Scopes"** button
2. Search for each scope name
3. Click the **"+"** button next to each required scope
4. Click **"Done"** when all scopes are added
5. Click **"Continue"** to proceed

### Step 6: Get Your API Credentials

After completing the app setup, you'll see the **"App Credentials"** page with three crucial pieces of information:

1. **Account ID**: A string starting with account ID format
2. **Client ID**: A long alphanumeric string
3. **Client Secret**: A long secret key (keep this secure!)

**Important Security Notes:**
- Never share your Client Secret publicly
- Store credentials securely
- Consider using environment variables for production deployments

### Step 7: Account Requirements

**Important**: Your Zoom account must meet these requirements:

- **Pro, Business, Education, or Enterprise account** (Basic accounts have limited API access)
- **Admin privileges** to access meeting reports and participant data
- **Meeting host or admin access** to the meetings you want to analyze

### Step 8: Testing Your Credentials

1. Copy your Account ID, Client ID, and Client Secret
2. Open the ZPA application
3. Go to **File → Settings**
4. Enter your credentials in the **"API Configuration"** tab
5. Click **"Test Connection"** to verify your setup
6. If successful, you'll see a green indicator

### Troubleshooting API Setup

**"Invalid credentials" error:**
- Double-check that you copied the credentials correctly
- Ensure there are no extra spaces or characters
- Verify your Zoom account has the required permissions

**"Insufficient privileges" error:**
- Your account needs Pro/Business/Enterprise level access
- Contact your Zoom administrator if you're in an organization
- Ensure you have admin privileges for the meetings you want to analyze

**"Scope not authorized" error:**
- Go back to your app settings and verify all required scopes are added
- Some scopes may require admin approval in enterprise accounts

### Meeting Access Requirements

To analyze polls from a meeting, you need:

- **Meeting Host Access**: You hosted the meeting, OR
- **Admin Access**: You have admin privileges in the Zoom account, OR
- **Shared Access**: The meeting host has granted you access

The meeting must also:
- Have ended (live meetings cannot be analyzed)
- Contain at least one poll
- Be accessible to your Zoom account

## Configuration

### Command Line Options

You can specify a custom INI file path when starting the application:

```bash
# Use a custom configuration file
zpa --ini-file /path/to/your/config.ini

# Or with the module syntax
python -m src.zpa --ini-file /path/to/your/config.ini
```

### Settings Dialog

On first run, go to **File → Settings** to configure:

**API Configuration Tab:**
- **Zoom API Credentials**: Account ID, Client ID, Client Secret
- **Connection Status**: Visual indicator with test button

**Application Tab:**
- **Meeting ID**: The Zoom meeting ID you want to analyze
- **Excluded Names**: Comma-separated list of participants to exclude
- **Poll Question Filter**: Filter polls by question text

**GUI Tab:**
- **Language**: Choose from English, German, or Greek
- **Theme**: Light, Dark, Solarized Light, or Solarized Dark
- **Font Size**: Adjustable table font size (6-16pt)
- **UI Font Size**: Adjustable interface font size (7-18pt)
- **Window Height**: Maximum window height (400-1200px)

**Export Tab:**
- **CSV Separator**: Choose comma, semicolon, or tab
- **Export Formats**: CSV, JSON, YAML, XML support

Settings are automatically saved to a configuration file with organized sections for better management.

## Usage

1. **Configure API**: Enter your Zoom API credentials in Settings
2. **Set Meeting ID**: Enter the meeting ID you want to analyze
3. **Load Data**: Click "Load Data" to fetch poll results from Zoom
4. **Analyze Results**: View poll responses in the interactive table
5. **Export Data**: Save results as CSV with UTF-8 encoding

## Data Processing

The application processes Zoom poll data to provide:

- Individual poll responses per participant
- Question and answer mapping  
- Participant information
- Response timestamps
- Statistical summaries

## File Structure

The project follows a clean, organized structure with separation of concerns:

```
ZPA/
├── src/zpa/
│   ├── __init__.py              # Package initialization
│   ├── __main__.py              # Module entry point
│   ├── main.py                  # Main application with CLI support
│   ├── core/                    # Core business logic
│   │   ├── __init__.py
│   │   ├── zoom_api.py          # Zoom API client
│   │   ├── data_processor.py    # Data analysis and utilities
│   │   └── export_manager.py    # Multi-format export handling
│   ├── ui/                      # User interface components
│   │   ├── __init__.py
│   │   ├── settings_dialog.py   # Settings configuration UI
│   │   ├── poll_table.py        # Data table widget with theming
│   │   ├── raw_data_dialog.py   # Raw data viewer
│   │   └── components/          # Reusable UI components
│   │       ├── __init__.py
│   │       └── status_led.py    # Status indicator component
│   ├── utils/                   # Utility modules
│   │   ├── __init__.py
│   │   ├── theme_manager.py     # Dynamic theme management
│   │   └── settings_manager.py  # Settings persistence
│   └── resources/              # Static resources
│       ├── themes/             # JSON theme definitions
│       │   ├── light.json      # Light theme
│       │   ├── dark.json       # Dark theme
│       │   ├── solarized-light.json
│       │   └── solarized-dark.json
│       ├── icons/              # Application icons
│       └── translations/       # Multi-language support
│           ├── __init__.py
│           ├── en.json         # English translations
│           ├── de.json         # German translations
│           └── el.json         # Greek translations
├── scripts/                    # Build, code-signing and diagnostic helpers
├── tests/                      # pytest suite
├── .github/                    # CI/CD workflows, Dependabot, issue templates
├── pyproject.toml              # Project configuration
├── uv.lock                     # Locked dependency versions
├── README.md                   # This file
└── LICENSE                     # GPL-3.0 license text
```

## Recent Improvements

### Version 2.0 Updates

**Enhanced Theme System:**
- Dynamic JSON-based theme loading with 4 built-in themes
- Poll table color integration for visual consistency
- Easy theme customization through JSON files
- Automatic system theme detection

**Code Architecture Improvements:**
- Organized folder structure with separation of concerns
- Consolidated duplicate code and removed unused imports
- Added utility functions for common operations
- Improved error handling and maintainability

**User Experience Enhancements:**
- Command-line argument support for custom INI files
- Responsive UI with auto-resizing tables
- Visual row coloring for poll responses (answered/unanswered/excluded)
- Enhanced status indicators with unified LED components

**Export Capabilities:**
- Multiple export formats (CSV, JSON, YAML, XML)
- UTF-8 encoding support
- Configurable CSV separators

**Performance Optimizations:**
- Reduced code duplication by ~150 lines
- Consolidated datetime parsing utilities
- Optimized column sizing algorithms
- Improved memory usage through better component reuse

## Building Standalone Executables

You can create standalone executables for Windows, macOS, and Linux that include Python and all dependencies. Users can run these without installing Python.

### Quick Build Commands

```bash
# Install build dependencies first
uv sync --group build

# Build for current platform
python scripts/build_executable.py

# Build with INI configuration file
python scripts/build_executable.py --include-ini

# Build for specific platform
python scripts/build_executable.py --platform windows

# Clean build artifacts
python scripts/build_executable.py --clean
```

### Manual Building

```bash
# Install build dependencies
uv sync --group build

# Activate virtual environment (Windows)
.venv\Scripts\Activate.ps1

# Build executable for current platform
python scripts/build_executable.py

# Clean build artifacts
python scripts/build_executable.py --clean
```

### Build Options

- `--include-ini`: Bundle an INI configuration file with the executable. **Never bundle an INI that contains credentials into an exe you share** - anyone can extract it.
- `--ini-path <path>`: Specify custom INI file location (default: `ZPA.ini`)
- `--platform <platform>`: Target platform (windows/macos/linux)
- `--clean`: Remove build artifacts

### Output Files

Executables are created in the `dist/` directory:

- **Windows**: `ZPA.exe`
- **macOS**: `ZPA.app` (application bundle)
- **Linux**: `ZPA` (executable binary)

### GitHub Actions

| Workflow | Trigger | What it does |
| --- | --- | --- |
| [CI](.github/workflows/ci.yml) | Push to `main`, pull requests | pre-commit hooks (ruff lint + format, YAML/JSON/TOML checks, zizmor workflow audit), gitleaks scan of the full history, pytest, test build of `ZPA.exe` (downloadable as workflow artifact) |
| [Release](.github/workflows/release.yml) | Tag `v*` | Checks the tag against `__version__`, builds `ZPA.exe`, creates a SHA-256 checksum and a build provenance attestation, publishes the GitHub release with generated notes |
| [CodeQL](.github/workflows/codeql.yml) | Push, pull requests, weekly | Static security analysis of the Python code and the workflows |
| [Dependency review](.github/workflows/dependency-review.yml) | Pull requests | Fails if a pull request adds dependencies with known vulnerabilities |

[Dependabot](.github/dependabot.yml) updates the Python dependencies (`uv.lock`), GitHub Actions and pre-commit hooks weekly.

To publish a release, bump `__version__` in `src/zpa/__init__.py`, merge to `main` and push a matching tag:

```bash
git tag v2.1.0
git push origin v2.1.0
```

## Development

### Setting up development environment

```bash
# Install the app with the development tools (ruff, pytest, pre-commit)
uv sync

# Run all checks automatically on every commit
uv run pre-commit install

# Lint, format and secret-scan all files
uv run pre-commit run --all-files

# Run tests
uv run pytest
```

### Building for distribution

```bash
# Build wheel and source distribution
uv build

# Install from local build
uv pip install dist/zpa-*.whl
```

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the development setup, the quality checks and the release process. Report security issues privately as described in [SECURITY.md](SECURITY.md).

## Troubleshooting

### API and Authentication Issues

**"Invalid credentials" or "Authentication failed"**
- Verify your Account ID, Client ID, and Client Secret are correct
- Ensure there are no extra spaces when copying credentials
- Check that your Zoom app has the required scopes enabled
- Test credentials using the "Test Connection" button in Settings

**"Insufficient privileges" or "Access denied"**
- Your Zoom account needs Pro, Business, Education, or Enterprise level
- Ensure you have admin privileges or are the meeting host
- Contact your Zoom administrator for proper permissions
- Verify the meeting ID belongs to your account or organization

**"Scope not authorized"**
- Return to your Zoom app settings and verify all required scopes are added:
  - `meeting:read:admin`
  - `report:read:admin`
- Some enterprise accounts require admin approval for new scopes

### Meeting Data Issues

**"No meeting data found" or "Meeting not accessible"**
- Verify the meeting ID is correct (11-digit number)
- Ensure the meeting has ended (live meetings cannot be analyzed)
- Check that the meeting contains polls
- Confirm your account has access to view the meeting

**"No poll data available"**
- The meeting must have had active polls during the session
- Polls must have received at least one response
- Verify the meeting ended properly (abruptly ended meetings may lose data)

### Application Issues

**"Settings not saving" or "Configuration reset"**
- Check write permissions in the application directory
- Ensure the INI file isn't marked as read-only
- Try running the application with administrator privileges
- Use a custom INI file path with `--ini-file` argument

**"Theme not applying" or "Display issues"**
- Restart the application after changing themes
- Check that theme JSON files exist in `resources/themes/`
- Try switching to a different theme to isolate the issue
- Reset to default theme if custom theme files are corrupted

**"Export failures" or "File save errors"**
- Ensure you have write permissions to the export location
- Check that the target directory exists
- Avoid special characters in file names
- Try different export formats (CSV, JSON, YAML, XML)
- Verify sufficient disk space

**"Font or display scaling issues"**
- Adjust font sizes in Settings → GUI tab
- Try different UI font sizes (7-18pt range)
- Check system display scaling settings
- Reset window height in Settings if table appears cut off

### Network and Connectivity

**"SSL/Connection errors" or "Network timeout"**
- Check your internet connection
- Verify firewall settings allow HTTPS connections to `api.zoom.us`
- Try connecting from a different network
- Check if your organization blocks API access
- Wait a few minutes and retry (Zoom API has rate limits)

**"Rate limit exceeded"**
- Zoom API has usage limits per app and per user
- Wait 1-2 minutes before making another request
- Reduce frequency of data loading operations
- Contact Zoom support if limits are consistently exceeded

### Performance Issues

**"Application running slowly" or "High memory usage"**
- Close other applications to free up system resources
- Avoid loading very large meetings (>500 participants)
- Restart the application periodically for long sessions
- Check system requirements (Python 3.8+, PyQt6 6.5.0+)

**"Table loading slowly" or "UI freezing"**
- Enable debug mode to see processing details
- Try excluding large numbers of participants in Settings
- Restart application if UI becomes unresponsive
- Consider processing smaller meeting segments

### Debug Mode

Enable debug mode in **Settings → Application** to see:
- Detailed API request/response information
- Data processing steps and timing
- Error stack traces with full details
- Meeting data structure and content
- Theme loading and application details

Debug output appears in the console when running from command line:
```bash
python -m src.zpa
```

## License

Copyright (C) 2024-2026 Marcel Vilas

ZPA is free software: you can redistribute it and/or modify it under the terms of the [GNU General Public License](LICENSE) as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. Anyone who distributes a modified version must make its source code available under the same license.

ZPA is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

ZPA is not affiliated with or endorsed by Zoom Video Communications, Inc.

## Acknowledgments

- Built with [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) (GPL v3) and Qt (LGPL v3) for the GUI framework
- Uses [Zoom API](https://developers.zoom.us/docs/api/) for meeting data access
- Inspired by the need for better poll analysis tools

## Support

If you encounter any issues or have feature requests, please [open an issue](https://github.com/bigmars86/ZPA/issues) on GitHub.
