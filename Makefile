PYTHON = python3
VENV_NAME = venv
VENV_BIN = $(VENV_NAME)/bin
VENV_PYTHON = $(VENV_BIN)/python3
VENV_PIP = $(VENV_BIN)/pip

.PHONY: setup server run-dev run-player clean

setup:
	@echo "========================================"
	@echo "Step 1: Checking System Dependencies..."
	@echo "========================================"
	@if [ "$$(uname)" = "Linux" ]; then \
		echo "Detected Linux. Checking for python3-tk..."; \
		sudo apt-get update && sudo apt-get install -y python3-tk || echo "⚠️  Sudo failed or skipped. Assuming Tkinter is already installed (Standard on Workstations)."; \
	else \
		echo "Not Linux (Mac/Windows). Skipping apt-get."; \
	fi

	@echo "========================================"
	@echo "Step 2: Creating Virtual Environment..."
	@echo "========================================"
	$(PYTHON) -m venv $(VENV_NAME)
	
	@echo "Step 3: Installing Python Requirements..."
	$(VENV_PYTHON) -m pip install --upgrade pip
	@if [ -f requirements.txt ]; then $(VENV_PIP) install -r requirements.txt; fi
	
	@echo "========================================"
	@echo "Setup Complete!"
	@echo "========================================"

server:
	$(VENV_PYTHON) server/server.py

dev:
	$(VENV_PYTHON) client_dev/dev_client.py 

player:
	$(VENV_PYTHON) client_player/player_client.py 

clean:
	rm -rf $(VENV_NAME)
	rm -rf server/server_data
	rm -rf client_player/downloads
	find . -type d -name "__pycache__" -exec rm -rf {} +