# Scripts

This directory contains utility scripts for the AfterIDE project.

## Files

- **run_tests.sh** - Unified test runner script that executes both backend and frontend tests
- **run_terminal_tests.py** - Python script for running comprehensive terminal-specific tests

## Usage

### Running All Tests
```bash
cd scripts
./run_tests.sh
```

### Running Terminal Tests Only
```bash
cd scripts
python run_terminal_tests.py
```

### Installing Test Dependencies
```bash
cd scripts
./run_tests.sh --install-deps
```

## Notes

- Make sure to run these scripts from the `scripts/` directory
- The scripts automatically handle path navigation to the backend and frontend directories
- Test configuration files are located in the `../config/` directory 