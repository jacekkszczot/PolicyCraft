# Windows Installation Guide for PolicyCraft

This guide will help you set up PolicyCraft on a Windows system using WSL2 (Windows Subsystem for Linux 2).

## Why WSL2?

We recommend using WSL2 for the best development experience on Windows. Here's why:

1. **Better Compatibility** - Many development tools and Python packages are designed to run on Linux first. WSL2 gives you a full Linux environment that works seamlessly with these tools.

2. **Consistent Environment** - It ensures your local setup matches the production environment, which typically runs on Linux. This means fewer "it works on my machine" issues.

3. **Easier Setup** - Some packages require compilation during installation. WSL2 handles this automatically, while native Windows might need additional configuration.

4. **Performance** - WSL2 offers near-native Linux performance, especially for file operations and running services like MongoDB.

5. **No Virtual Machine Overhead** - Unlike traditional virtual machines, WSL2 is lightweight and starts up quickly.

If you prefer not to use WSL2, you'll need to set up MongoDB and other dependencies manually on Windows, which can be more complex and less reliable.

## Prerequisites

1. **Enable WSL2 (Windows Subsystem for Linux 2)**
   - Open PowerShell as Administrator and run:
     ```powershell
     wsl --install
     ```
   - Restart your computer when prompted
   - After restart, complete the Ubuntu setup by creating a username and password

2. **Install Python 3.8 or later**
   - Download from [python.org](https://www.python.org/downloads/windows/)
   - During installation, make sure to check "Add Python to PATH"

3. **Install Git**
   - Download from [git-scm.com](https://git-scm.com/download/win)
   - Use default settings during installation

## Installation Steps

1. **Open WSL2 Terminal**
   - Press `Win + R`, type `wsl` and press Enter

2. **Clone the Repository**
   ```bash
   cd ~
   git clone https://github.com/jacekkszczot/PolicyCraft.git
   cd PolicyCraft
   ```

3. **Run the Windows Installation Script**
   ```bash
   python windows_setup.py
   ```
   
   Or use the PowerShell script:
   ```powershell
   .\windows_install.ps1
   ```

4. **Start the Application**
   ```bash
   python app.py
   ```

5. **Access the Application**
   - Open your web browser and go to: http://localhost:5001
   - Login with:
     - Email: admin@policycraft.ai
     - Password: admin1

## Troubleshooting

### WSL2 Installation Issues
- Ensure virtualization is enabled in BIOS/UEFI
- Make sure you're running Windows 10 version 2004 or later, or Windows 11

### MongoDB Connection Issues
- The script will attempt to start MongoDB automatically
- If you encounter connection issues, manually start MongoDB in WSL2:
  ```bash
  sudo service mongod start
  ```

### Python Dependencies
If you get Python package errors, make sure to use the Windows-specific requirements file:
```bash
pip install -r requirements_windows.txt

# Install language model for NLP
python -m spacy download en_core_web_sm
```

### Known Issues

#### python-magic Installation
If you encounter issues with `python-magic`, you may need to install it manually:
1. First install the Windows binary:
   ```bash
   pip install python-magic-bin
   ```
2. Then install the Python package:
   ```bash
   pip install python-magic
   ```

#### WSL2 File System Performance
For better performance when working with WSL2:
1. Store your project in the WSL2 filesystem (not in the Windows filesystem mounted in WSL)
2. Avoid running the application from `/mnt/c/` or other mounted Windows drives
