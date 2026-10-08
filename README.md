# ThreatLens

ThreatLens is organized as a main Git repository with the security tools kept
in their upstream repositories as Git submodules. The PySide6 application is
in [`WEB-PENTEST-GUI`](./WEB-PENTEST-GUI/README.md).

## Clone the complete project

```powershell
git clone --recurse-submodules https://github.com/yashr3537/ThreatLens.git
cd ThreatLens
```

If you already cloned without the submodules:

```powershell
git submodule update --init --recursive
```

## Run the GUI

Follow the setup instructions in
[`WEB-PENTEST-GUI/README.md`](./WEB-PENTEST-GUI/README.md). The GUI source,
tool catalog, test suite, and Windows packaging spec are all kept inside
`WEB-PENTEST-GUI`.

The root `.gitignore` excludes only local environments, caches, and generated
build/runtime artifacts. Project `README.md` files are intentionally tracked.
