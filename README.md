# Library Barcode Label Generator

A professional, standalone Windows desktop application designed to easily generate and print bulk barcode labels for libraries and educational institutions.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-Windows_10%20|%2011-lightgrey)
![Build](https://img.shields.io/badge/build-passing-brightgreen)

---

## ✨ Features

- **Multiple Barcode Standards:** Supports Code 128, Code 39, EAN-13, and ISBN.
- **Bulk Generation:** Import data seamlessly from `.xlsx`, `.csv`, or `.txt` files to generate thousands of labels at once.
- **Visual Template Editor:** A fully interactive, drag-and-drop web-based editor to design custom label layouts.
- **Print-Ready PDFs:** Generates high-quality, perfectly aligned PDFs ready for immediate printing.
- **Customizable Pages:** Configure page size (A4, Letter), margins, grid layouts (rows/columns), and label padding.
- **Standalone Desktop App:** Packaged as a native Windows application with a beautiful frameless dark-mode UI. No Python installation required on the end-user machine.

## 🚀 Installation

### Option 1: Using the Installer (Recommended)
1. Download the latest `LibraryBarcodeGenerator_Setup.exe` from the releases page.
2. Run the installer.
3. Launch the application from your Desktop or Start Menu.

### Option 2: Running from Source
If you wish to run or modify the application from source, ensure you have Python 3.9+ installed.

1. Clone the repository:
   ```bash
   git clone https://github.com/Nazimcp-git/barcode-maker.git
   cd barcode-maker
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the desktop application:
   ```bash
   python desktop.py
   ```

## 🛠️ Building the Executable

To compile the Python application into a standalone Windows `.exe` and create the installer:

### 1. Compile the Application
We use PyInstaller to bundle the application. A custom `build.spec` file is included to properly bundle fonts and static assets.
```bash
pyinstaller --clean build.spec
```
This will generate the compiled application inside the `dist/LibraryBarcodeGenerator/` directory.

### 2. Create the Installer
We use **Inno Setup 6** to create the Windows setup executable.
Ensure Inno Setup 6 is installed on your system, then compile the `installer.iss` script:

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```
*(Note: Update the path to `ISCC.exe` based on your installation directory).*
The final installer will be generated in the `installer_output/` folder.

## 📁 Project Structure

```
├── app.py                     # Flask backend server
├── desktop.py                 # PyWebView desktop wrapper & entry point
├── config.py                  # Application configuration & path resolution
├── build.spec                 # PyInstaller bundling specification
├── installer.iss              # Inno Setup installer script
├── routes/                    # Flask API & HTML rendering routes
├── services/                  # Core logic (PDF builder, Barcode generator)
├── static/                    # Frontend CSS, JS, and Images
├── templates/                 # HTML UI views (Editor, Home page)
└── saved_templates/           # JSON files containing saved user layouts
```

## 💻 Tech Stack

- **Backend:** Python, Flask
- **Desktop Wrapper:** PyWebView (Edge Chromium)
- **Frontend:** Vanilla JavaScript, HTML5, CSS3 (Glassmorphism UI)
- **PDF Generation:** ReportLab
- **Barcodes:** Python-Barcode
- **Data Parsing:** Pandas, OpenPyXL

## 👨‍💻 Developer

**Nazim Cp**
Full-stack developer passionate about building tools that simplify workflows for libraries and educational institutions.

## 📄 License
This project is licensed under the MIT License.
