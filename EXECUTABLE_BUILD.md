# Executable Creation System

This document explains the standalone executable creation system for ZPA (Zoom Poll Analyzer).

## Overview

The application now supports creating standalone executables that bundle Python, all dependencies, and the application code into single distributable files. Users can run these without installing Python or any dependencies.

## Components

### 1. Build Script (`scripts/build_executable.py`)

A comprehensive Python script that uses PyInstaller to create executables.

**Features:**
- Cross-platform support (Windows, macOS, Linux)
- Platform auto-detection
- INI file inclusion options
- Clean build artifacts functionality
- Comprehensive error handling and progress reporting

**Usage:**
```bash
python scripts/build_executable.py [options]
```

### 2. Project Configuration (`pyproject.toml`)

The `build` dependency group contains the build tools:

**Build Dependencies:**
- `pyinstaller>=5.0` - For creating executables
- `setuptools` - For cross-platform compatibility

The executable version is read from `__version__` in `src/zpa/__init__.py`, the single source of the version.

### 3. GitHub Actions Workflows

#### Release Workflow (`.github/workflows/release.yml`)
- Triggers on version tags (e.g., `v2.1.0`) that must match `__version__`
- Builds `ZPA.exe` on Windows
- Publishes a GitHub release with the exe, a SHA-256 checksum and a build provenance attestation

#### CI Workflow (`.github/workflows/ci.yml`)
- Runs on pushes to `main` and on pull requests
- Lints, tests and test-builds `ZPA.exe` (available as a workflow artifact)

### 4. Convenience Scripts

#### Windows Batch Script (`build.bat`)
Simple batch file for Windows users:
```batch
build.bat          # Build executable
build.bat clean    # Clean artifacts
build.bat include-ini  # Build with INI file
```

#### Unix Shell Script (`build.sh`)
Shell script for macOS and Linux:
```bash
./build.sh         # Build executable
./build.sh clean   # Clean artifacts
./build.sh include-ini  # Build with INI file
```

## Build Process

### Local Building

1. **Install dependencies:**
   ```bash
   uv sync --group build
   ```

2. **Build executable:**
   ```bash
   uv run python scripts/build_executable.py
   ```

3. **Output location:**
   - Executables are created in `dist/` directory
   - Build artifacts in `build/` directory
   - Spec files in `specs/` directory

### Automated Releases

1. **Bump `__version__`** in `src/zpa/__init__.py` and merge to `main`.

2. **Create and push a matching tag:**
   ```bash
   git tag v2.1.0
   git push origin v2.1.0
   ```

3. **GitHub Actions will:**
   - Verify that the tag matches `__version__`
   - Build `ZPA.exe` on Windows
   - Create a GitHub release with the exe, its SHA-256 checksum and generated release notes

## Executable Details

### Windows (`ZPA.exe`)
- Single executable file
- No console window (GUI only)
- Includes all resources and themes
- Size: ~150-200 MB (includes Python runtime)

### macOS (`ZPA.app`)
- Application bundle
- Universal binary (Intel + Apple Silicon)
- Includes all resources and themes
- Size: ~200-250 MB (includes Python runtime)

### Linux (`ZPA`)
- Single executable binary
- Requires GUI environment (X11/Wayland)
- Includes all resources and themes
- Size: ~150-200 MB (includes Python runtime)

## Included Resources

All executables include:
- Theme files (`resources/themes/`)
- Translation files (`resources/translations/`)
- Icons (`resources/icons/`)
- Application icon
- Optional: INI configuration file

## Distribution

### GitHub Releases
- Automatic releases via GitHub Actions
- Download links for all platforms
- Release notes with installation instructions

### Manual Distribution
- Copy executable files directly
- No installation required
- Can be run from any location

## INI File Handling

### Including INI in Executable
```bash
python scripts/build_executable.py --include-ini --ini-path "my-config.ini"
```

### Benefits:
- Pre-configured settings for users
- Consistent configuration across deployments
- Simplified setup for end users

## Troubleshooting

### Build Issues

**"PyInstaller not found"**
- Install build dependencies: `uv sync --group build`
- Or manually: `pip install pyinstaller>=5.0`

**"Missing modules in executable"**
- Check `hidden_imports` in build script
- Add missing modules to the list

**"Resources not found"**
- Verify paths in `datas` section of spec file
- Check resource files exist in source directory

### Runtime Issues

**"Application won't start"**
- Run from command line to see error messages
- Check antivirus software (may block PyInstaller executables)
- Verify all resources are properly bundled

**"Theme/translation issues"**
- Ensure resource files are included in build
- Check file paths in application code
- Verify resource loading logic

## Cross-Platform Considerations

### Windows
- Antivirus software may flag PyInstaller executables
- Consider code signing for production releases
- Test on Windows 10 and 11

### macOS
- Application may be blocked by Gatekeeper
- Consider code signing and notarization for distribution
- Test on both Intel and Apple Silicon Macs

### Linux
- Different distributions may have different requirements
- Ensure GUI libraries are available on target systems
- Test on major distributions (Ubuntu, Fedora, etc.)

## Future Enhancements

1. **Code Signing**: Add digital signatures for Windows and macOS
2. **Installer Creation**: Create installers instead of single executables
3. **Auto-Updates**: Implement automatic update checking
4. **Compression**: Optimize executable size with UPX or similar
5. **Docker**: Add containerized build environment for consistent builds

## Performance Notes

- First startup may be slower due to extraction
- Subsequent starts are faster
- Executables are larger than Python scripts but more portable
- Memory usage similar to regular Python application
