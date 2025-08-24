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
  engine: wiredTiger

# where to write logging data.
systemLog:
  destination: file
  logAppend: true
  path: $MONGO_LOG_DIR/mongod.log
  logRotate: reopen
  timeStampFormat: iso8601-utc

# network interfaces
net:
  port: 27017
  bindIp: 127.0.0.1
  ipv6: false
  unixDomainSocket:
    enabled: true
    pathPrefix: /tmp
    filePermissions: 0700

# how the process runs
processManagement:
  fork: true
  pidFilePath: $MONGO_DATA_DIR/mongod.pid
  timeZoneInfo: /usr/share/zoneinfo

# security:
#   authorization: enabled

# operationProfiling:
#   mode: slowOp
#   slowOpThresholdMs: 100
#   slowOpSampleRate: 0.5

# replication:
#   replSetName: rs0
EOL

echo "MongoDB configuration file created at: $MONGO_CONF_FILE"

# Create a script to start MongoDB with the custom data directory
START_SCRIPT="$HOME/start_mongodb.sh"
cat > "$START_SCRIPT" << 'EOL'
#!/bin/bash

# Configuration
MONGO_DATA_DIR="$HOME/mongodb_data"
MONGO_LOG_DIR="$HOME/mongodb_logs"
MONGO_PID_FILE="$MONGO_DATA_DIR/mongod.pid"

# Find MongoDB binary
MONGODB_BIN=$(which mongod)
if [ -z "$MONGODB_BIN" ]; then
    echo "MongoDB is not installed or not in PATH. Please install MongoDB first."
    echo "On macOS with Homebrew: brew install mongodb-community"
    exit 1
fi

# Check if MongoDB is already running
if [ -f "$MONGO_PID_FILE" ]; then
    PID=$(cat "$MONGO_PID_FILE")
    if ps -p $PID > /dev/null; then
        echo "MongoDB is already running with PID $PID"
        exit 0
    else
        # Remove stale PID file
        rm -f "$MONGO_PID_FILE"
    fi
fi

# Ensure directories exist
mkdir -p "$MONGO_DATA_DIR"
mkdir -p "$MONGO_LOG_DIR"

# Start MongoDB
echo "Starting MongoDB with data directory: $MONGO_DATA_DIR"
"$MONGODB_BIN" --dbpath "$MONGO_DATA_DIR" \
               --logpath "$MONGO_LOG_DIR/mongod.log" \
               --pidfilepath "$MONGO_PID_FILE" \
               --fork \
               --bind_ip 127.0.0.1 \
               --logappend

# Check if MongoDB started successfully
if [ $? -eq 0 ]; then
    echo "MongoDB started successfully"
    echo "Logs: $MONGO_LOG_DIR/mongod.log"
    echo "Data: $MONGO_DATA_DIR"
    echo "PID: $(cat $MONGO_PID_FILE 2>/dev/null || echo 'Unknown')"
    echo "Connect using: mongosh"
else
    echo "Failed to start MongoDB. Check the log file: $MONGO_LOG_DIR/mongod.log"
    exit 1
fi
EOL

# Make the scripts executable
chmod +x "$START_SCRIPT"
chmod +x "$HOME/start_mongodb.sh"

echo "Setup complete!"
echo "To start MongoDB, run: $HOME/start_mongodb.sh"
echo "To connect: mongosh --host 127.0.0.1 --port 27017"
echo "To stop MongoDB: Press Ctrl+C in the terminal where it's running"
echo "\nNote: MongoDB will run in the foreground. For production use, consider setting up a proper service."
