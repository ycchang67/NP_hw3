.PHONY: clean server dev player init
# Clean up compiled files and data
clean:
	rm -rf __pycache__
	rm -rf common/__pycache__
	rm -rf server/__pycache__
	rm -rf client_dev/__pycache__
	rm -rf client_player/__pycache__
	rm -rf server/server_data
	rm -rf client_player/downloads

# Run the Server
server:
	python3 server/server.py

# Run the Developer Client
dev:
	python3 client_dev/dev_client.py

# Run the Player Client
player:
	python3 client_player/player_client.py

# Create a sample game file for testing upload if not exists
init:
	mkdir -p server_data
	mkdir -p downloads