# 🌌 LV Nexus: Premium Windows Optimizer

![LV Nexus Banner](https://img.shields.io/badge/Version-2.1.0_Premium-blueviolet?style=for-the-badge)
![License](https://img.shields.io/badge/License-Commercial-green?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows_10%2F11-0078D4?style=for-the-badge)

**LV Nexus (v2.1.0 Premium)** is an elite, high-performance Windows optimization suite engineered for developers, gamers, and power users. Built on a modular, thread-safe Python engine and a high-fidelity glassmorphic HTML5 dashboard, it provides kernel-level hardening, deep system hygiene, and real-time telemetry.

---

## ✨ Premium Features Fully Integrated

- **🎯 Advanced Process Priority Manager**: Process Lasso-style real-time process monitoring and priority elevation (Gaming & Dev profiles).
- **🔒 Privacy Shield**: ShutUp10++ style telemetry disabling, cortana blocking, and tailored advertising tracking removal.
- **🛠️ Advanced System Tweaks**: Winaero-style hidden registry modifications to harden UI, network latency, and OS visual performance.
- **🫧 Deep Cleaner**: BleachBit-style deep system cache sanitization, GPU shader purge, and app-specific temp cleaner.
- **🌡️ Smart Temperature Adaptive Boost**: Multi-zone thermal telemetry (Cool, Warm, Hot) with automated background process throttling when hardware overheats.
- **🚀 Dual-Tier Optimization**:
  - **Quick Boost**: Rapid RAM reclamation.
  - **Master Optimize**: Deep kernel registry injections.
- **🛡️ Safety-First Architecture**:
  - Mandatory Windows Restore Points and timestamped Multi-Version Registry Backups.
- **📊 Real-time Telemetry**: Live CPU, RAM, GPU, and precise Thermal tracking.

---

## 🛠️ Installation & Build

### Prerequisites
- Python 3.10+
- Administrator Privileges (required for system modifications)

### Setup
```bash
# Clone the repository
git clone https://github.com/your-repo/lv-nexus.git
cd lv-nexus

# Install dependencies
pip install -r requirements.txt
```

### Production Build (EXE)
To generate a standalone, highly-optimized Windows executable:
```bash
python build.py
```
The output will be located in the `dist/` directory as `LV_Nexus.exe`.

---

## ⚠️ Important Warnings

> [!WARNING]
> **Registry Modifications**: This application modifies sensitive Windows Registry keys (Advanced Tweaks & Privacy Shield). Always ensure your Safety Backups are active.

> [!IMPORTANT]
> **UAC Elevation**: LV Nexus absolutely requires Administrator rights to interact with the Windows Kernel, manage UWP Bloatware, and handle system hardware telemetry.

> [!CAUTION]
> **Thermal Throttling**: The Smart Temperature Boost will automatically kill or downgrade non-critical apps if your CPU/GPU exceeds 80°C.

---

## 📜 License
**Commercial Enterprise License** — © 2026 LV Nexus Architecture. All rights reserved.

---

## 🤝 Credits
- **Core Engine**: Developed with Python, `psutil`, `wmi`, and `GPUtil`.
- **Frontend**: Premium Glassmorphism UI built with Vanilla JS & `pywebview`.
- **Design Architecture**: Pro Studio Dashboard / Cyberpunk Aesthetic.
