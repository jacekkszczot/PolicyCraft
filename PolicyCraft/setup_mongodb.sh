#!/bin/bash

# Create MongoDB data directory in the user's home folder
MONGO_DATA_DIR="$HOME/mongodb_data"
MONGO_LOG_DIR="$HOME/mongodb_logs"

# Create directories if they don't exist
mkdir -p "$MONGO_DATA_DIR"
mkdir -p "$MONGO_LOG_DIR"

echo "MongoDB data directory: $MONGO_DATA_DIR"
echo "MongoDB log directory: $MONGO_LOG_DIR"

# Create MongoDB configuration file
MONGO_CONF_FILE="$HOME/mongod.conf"
cat > "$MONGO_CONF_FILE" <<EOL
# mongod.conf

# for documentation of all options, see:
#   http://docs.mongodb.org/manual/reference/configuration-options/

# Where and how to store data.
storage:
  dbPath: $MONGO_DATA_DIR
  journal:
    enabled: true

# where to write logging data.
systemLog:
  destination: file
  logAppend: true
  path: $MONGO_LOG_DIR/mongod.log

# network interfaces
net:
  port: 27017
  bindIp: 127.0.0.1

# how the process runs
processManagement:
  timeZoneInfo: /usr/share/zoneinfo

# security:
#   authorization: enabled
EOL

echo "MongoDB configuration file created at: $MONGO_CONF_FILE"

# Create a script to start MongoDB with the custom data directory
START_SCRIPT="$HOME/start_mongodb.sh"
cat > "$START_SCRIPT" << 'EOL'
#!/bin/bash
MONGODB_BIN=$(which mongod)
if [ -z "$MONGODB_BIN" ]; then
    echo "MongoDB is not installed. Please install MongoDB first."
    echo "On macOS with Homebrew: brew install mongodb-community"
    exit 1
fi

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
CONF_FILE="$HOME/mongod.conf"

if [ ! -f "$CONF_FILE" ]; then
    echo "Error: MongoDB configuration file not found at $CONF_FILE"
    echo "Please run setup_mongodb.sh first"
    exit 1
fi

echo "Starting MongoDB with config: $CONF_FILE"
$MONGODB_BIN --config "$CONF_FILE"
EOL

# Make the scripts executable
chmod +x "$START_SCRIPT"
chmod +x "$HOME/start_mongodb.sh"

echo "Setup complete!"
echo "To start MongoDB, run: $HOME/start_mongodb.sh"
echo "To connect: mongosh --host 127.0.0.1 --port 27017"
echo "To stop MongoDB: Press Ctrl+C in the terminal where it's running"
echo "\nNote: MongoDB will run in the foreground. For production use, consider setting up a proper service."
