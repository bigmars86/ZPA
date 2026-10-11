#!/usr/bin/env python3
"""
Build script for creating standalone executables of ZPA (Zoom Poll Analyzer).
Uses PyInstaller to bundle Python, dependencies, and source code into single executables.
"""

import argparse
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path


class ExecutableBuilder:
    """Build standalone executables for ZPA (Zoom Poll Analyzer)"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.src_dir = self.project_root / "src"
        self.dist_dir = self.project_root / "dist"
        self.build_dir = self.project_root / "build"
        self.spec_dir = self.project_root / "specs"

        # Platform detection
        self.current_platform = self._detect_platform()

    def _detect_platform(self):
        """Detect current platform"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            return "unknown"

    def _ensure_directories(self):
        """Create necessary directories"""
        self.dist_dir.mkdir(exist_ok=True)
        self.spec_dir.mkdir(exist_ok=True)

    def _install_build_dependencies(self):
        """Install PyInstaller and build dependencies"""
        print("📦 Checking build dependencies...")

        # Check if PyInstaller is already available
        try:
            import PyInstaller

            print(f"✅ PyInstaller {PyInstaller.__version__} is already available")
            return
        except ImportError:
            pass

        # Try to install with pip if available
        try:
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "pyinstaller>=5.0",
                    "setuptools",
                ],
                check=True,
            )
            print("✅ Build dependencies installed successfully")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print("⚠️  Could not install dependencies with pip")
            print("   Please ensure PyInstaller is installed:")
            print("   - Run: uv sync --group build")
            print("   - Or: pip install pyinstaller>=5.0 setuptools")
            raise RuntimeError("PyInstaller is required but not available") from e

    def _create_version_file(self):
        """Create a Windows version-info resource so the built EXE carries
        proper metadata (product name, description, version).

        This makes the file look legitimate in Explorer's Properties dialog and
        reduces some antivirus heuristics. NOTE: it does NOT remove the Windows
        SmartScreen "unknown publisher" prompt - only code signing with a
        trusted certificate does that.
        """
        init_py = (self.src_dir / "zpa" / "__init__.py").read_text(encoding="utf-8")
        match = re.search(
            r"^__version__\s*=\s*[\"']([^\"']+)[\"']", init_py, re.MULTILINE
        )
        if not match:
            raise RuntimeError("__version__ not found in src/zpa/__init__.py")
        version = match.group(1)
        # Windows FILEVERSION needs four integers, e.g. "2.1.0rc1" -> (2, 1, 0, 0)
        parts = (re.findall(r"\d+", version)[:3] + ["0", "0", "0", "0"])[:4]
        vtuple = ", ".join(parts)
        content = (
            "# UTF-8\n"
            "VSVersionInfo(\n"
            "  ffi=FixedFileInfo(\n"
            f"    filevers=({vtuple}),\n"
            f"    prodvers=({vtuple}),\n"
            "    mask=0x3f,\n"
            "    flags=0x0,\n"
            "    OS=0x40004,\n"
            "    fileType=0x1,\n"
            "    subtype=0x0,\n"
            "    date=(0, 0)\n"
            "  ),\n"
            "  kids=[\n"
            "    StringFileInfo([\n"
            "      StringTable('040904b0', [\n"
            "        StringStruct('CompanyName', 'Zoom Poll Analyzer'),\n"
            "        StringStruct('FileDescription', 'Zoom Poll Analyzer (ZPA)'),\n"
            f"        StringStruct('FileVersion', '{version}.0'),\n"
            "        StringStruct('InternalName', 'ZPA'),\n"
            "        StringStruct('LegalCopyright', 'Zoom Poll Analyzer'),\n"
            "        StringStruct('OriginalFilename', 'ZPA.exe'),\n"
            "        StringStruct('ProductName', 'Zoom Poll Analyzer'),\n"
            f"        StringStruct('ProductVersion', '{version}.0'),\n"
            "      ])\n"
            "    ]),\n"
            "    VarFileInfo([VarStruct('Translation', [0x0409, 1200])])\n"
            "  ]\n"
            ")\n"
        )
        self.spec_dir.mkdir(exist_ok=True)
        version_file = self.spec_dir / "version_info.txt"
        with open(version_file, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Version info written: {version_file}")
        return version_file

    def _create_pyinstaller_spec(self, include_ini=False, ini_path=None):
        """Create PyInstaller spec file"""
        print("📝 Creating PyInstaller spec file...")

        # Data files to include
        datas = [
            # Theme files
            (str(self.src_dir / "zpa" / "resources" / "themes"), "resources/themes"),
            # Translation files
            (
                str(self.src_dir / "zpa" / "resources" / "translations"),
                "resources/translations",
            ),
            # Icons
            (str(self.src_dir / "zpa" / "resources" / "icons"), "resources/icons"),
        ]

        # Add INI file if requested
        if include_ini and ini_path:
            ini_abs_path = Path(ini_path).resolve()
            if ini_abs_path.exists():
                # Bundle as template inside the executable
                datas.append((str(ini_abs_path), "."))
                print(f"📄 Including INI template: {ini_abs_path}")
                print("   Will be copied to external location on first run")
            else:
                print(f"⚠️  INI file not found: {ini_abs_path}")
                print("   Build will continue without INI template")

        # Hidden imports for PyQt6 and other dependencies
        hidden_imports = [
            # PyQt6 modules
            "PyQt6.QtCore",
            "PyQt6.QtGui",
            "PyQt6.QtWidgets",
            # Standard library modules
            "requests",
            "urllib3",
            "yaml",
            "json",
            "csv",
            "configparser",
            "argparse",
            "pathlib",
            "datetime",
            "traceback",
            # Application modules - explicitly include all submodules
            "zpa",
            "zpa.main",
            "zpa.core",
            "zpa.core.zoom_api",
            "zpa.core.data_processor",
            "zpa.core.export_manager",
            "zpa.ui",
            "zpa.ui.settings_dialog",
            "zpa.ui.poll_table",
            "zpa.ui.raw_data_dialog",
            "zpa.ui.components",
            "zpa.ui.components.status_led",
            "zpa.utils",
            "zpa.utils.theme_manager",
            "zpa.utils.settings_manager",
            "zpa.utils.resource_paths",
            "zpa.resources",
            "zpa.resources.translations",
        ]

        # Convert Windows paths to forward slashes for the spec file
        # Use src/zpa/main.py as entry point
        main_py_path = str(self.project_root / "src" / "zpa" / "main.py").replace(
            "\\", "/"
        )
        project_root_path = str(self.project_root).replace("\\", "/")
        src_dir_path = str(self.src_dir).replace("\\", "/")
        icon_path = str(
            self.project_root / "src" / "zpa" / "resources" / "icons" / "zoom-icon.ico"
        ).replace("\\", "/")

        # Windows version-info resource (metadata only; not a code signature)
        version_line = ""
        if self.current_platform == "windows":
            version_path = str(self._create_version_file()).replace("\\", "/")
            version_line = f"    version=r'{version_path}',\n"

        # Build spec content with proper icon handling
        spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{main_py_path}'],
    pathex=['{project_root_path}', '{src_dir_path}'],
    binaries=[],
    datas={datas!r},
    hiddenimports={hidden_imports!r},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ZPA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
{version_line}    icon='{icon_path}',
)
"""

        # Add macOS app bundle for macOS
        if self.current_platform == "macos":
            spec_content += """
app = BUNDLE(
    exe,
    name='ZPA.app',
    icon='src/zpa/resources/icons/app.icns',
    bundle_identifier='com.zpa.app',
)
"""

        spec_file = self.spec_dir / "ZPA.spec"
        with open(spec_file, "w") as f:
            f.write(spec_content)

        return spec_file

    def _run_pyinstaller(self, spec_file):
        """Run PyInstaller with the spec file"""
        print("🔧 Running PyInstaller...")

        cmd = [
            sys.executable,
            "-m",
            "PyInstaller",
            str(spec_file),
            "--distpath",
            str(self.dist_dir),
            "--workpath",
            str(self.build_dir),
        ]

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=self.project_root)

        if result.returncode != 0:
            raise RuntimeError("PyInstaller failed!")

    def _post_process(self):
        """Post-process the built executable"""
        print("🎯 Post-processing executable...")

        # Determine executable name based on platform
        if self.current_platform == "windows":
            exe_name = "ZPA.exe"
        elif self.current_platform == "macos":
            exe_name = "ZPA.app"
        else:
            exe_name = "ZPA"

        exe_path = self.dist_dir / exe_name

        if exe_path.exists():
            print(f"✅ Executable created: {exe_path}")
            print(f"📏 Size: {self._get_file_size(exe_path)}")
        else:
            raise RuntimeError(f"Executable not found at {exe_path}")

        return exe_path

    def _get_file_size(self, path):
        """Get human-readable file size"""
        if path.is_dir():  # macOS app bundle
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
        else:
            size = path.stat().st_size

        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def clean(self):
        """Clean build artifacts"""
        print("🧹 Cleaning build artifacts...")

        dirs_to_clean = [self.build_dir, self.dist_dir, self.spec_dir]

        for dir_path in dirs_to_clean:
            if dir_path.exists():
                try:
                    shutil.rmtree(dir_path)
                    print(f"Removed: {dir_path}")
                except PermissionError:
                    print(f"⚠️  Could not remove {dir_path} (permission denied)")
                    print("   Please manually delete this directory if needed")
                except Exception as e:
                    print(f"⚠️  Could not remove {dir_path}: {e}")

        print("✅ Clean complete!")

    def build(self, include_ini=False, ini_path=None, platform_target=None):
        """Build executable for specified platform"""

        if platform_target and platform_target != self.current_platform:
            print("❌ Cross-platform building not supported in this script.")
            print(f"   Current platform: {self.current_platform}")
            print(f"   Target platform: {platform_target}")
            print("   Please run this script on the target platform.")
            return None

        try:
            print(
                f"🚀 Building ZPA (Zoom Poll Analyzer) executable for {self.current_platform}..."
            )

            self._ensure_directories()
            self._install_build_dependencies()

            spec_file = self._create_pyinstaller_spec(include_ini, ini_path)
            self._run_pyinstaller(spec_file)
            exe_path = self._post_process()

            print(f"🎉 Build complete! Executable: {exe_path}")
            return exe_path

        except Exception as e:
            print(f"❌ Build failed: {e}")
            return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Build standalone executables for ZPA (Zoom Poll Analyzer)"
    )

    parser.add_argument(
        "--include-ini",
        nargs="?",
        const="zpa.ini",
        metavar="PATH",
        help="Include an INI configuration file in the executable. "
        "Optionally specify path (default: zpa.ini)",
    )

    parser.add_argument(
        "--platform",
        choices=["windows", "macos", "linux", "all"],
        help="Target platform (default: current platform)",
    )

    parser.add_argument(
        "--clean", action="store_true", help="Clean build artifacts and exit"
    )

    args = parser.parse_args()

    builder = ExecutableBuilder()

    if args.clean:
        builder.clean()
        return

    # Handle INI inclusion
    include_ini = args.include_ini is not None
    ini_path = args.include_ini if include_ini else None

    # Build for specified platform(s)
    if args.platform == "all":
        print(
            "❌ Building for all platforms requires running on each platform separately."
        )
        print("   Use GitHub Actions for automated multi-platform builds.")
        sys.exit(1)

    target_platform = args.platform or builder.current_platform

    result = builder.build(
        include_ini=include_ini, ini_path=ini_path, platform_target=target_platform
    )

    if result:
        print(f"\n🎯 Ready to distribute: {result}")
        print(
            "   The executable includes Python, all dependencies, and the application."
        )
        print("   No additional installation required on target systems!")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
