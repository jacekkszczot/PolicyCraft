# PolicyCraft Troubleshooting Guide
# ===================================
# Comprehensive guide for resolving common issues and known problems
#
# Author: Jacek Robert Kszczot
# Project: MSc Data Science & AI - COM7016
# University: Leeds Trinity University
# Last Updated: August 2025

## Overview

This guide addresses common issues encountered when setting up and running PolicyCraft, including recently resolved problems and their solutions.

## Recently Resolved Issues

### 1. PyMongo Collection Boolean Testing Error

**Problem**: `NotImplementedError: Collection objects do not implement truth value testing or bool()`

**Root Cause**: PyMongo Collection objects cannot be used directly in boolean conditions (e.g., `if mongo_db.analyses:`)

**Solution**: Use explicit `is not None` comparison instead of boolean testing
```python
# ❌ INCORRECT - causes crash
if mongo_db.is_connected() and mongo_db.analyses:

# ✅ CORRECT - safe comparison
if mongo_db.is_connected() and mongo_db.analyses is not None:
```

**Files Modified**:
- `src/admin/routes.py` - Dashboard and reset_progress functions
- `src/database/mongo_operations.py` - Connection handling improvements

**Status**: ✅ RESOLVED

### 2. Chart Generation and Display Issues

**Problem**: Charts not displaying in web interface, export errors

**Root Causes**:
1. `ChartGenerator` returning Plotly Figure objects instead of JSON strings
2. Template trying to render Plotly objects directly
3. Export system expecting different data format

**Solutions**:
1. **ChartGenerator Updates**: Methods now return Plotly Figure objects
2. **Template Updates**: `results.html` uses `|tojson|safe` for proper rendering
3. **Export Integration**: Automatic JSON conversion for web display

**Files Modified**:
- `src/visualisation/charts.py` - Return type changes and error fixes
- `src/web/templates/results.html` - Template rendering updates
- `app.py` - Chart data serialization in `_build_results_payload`

**Status**: ✅ RESOLVED

### 3. MongoDB Connection Resilience

**Problem**: Application crashes when MongoDB is unavailable

**Solution**: Graceful degradation with connection status checking
```python
class MongoOperations:
    def __init__(self):
        try:
            self.client = MongoClient(uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self._connected = True
        except Exception:
            self._connected = False
            self.client = None
            self.db = None
    
    def is_connected(self):
        return self._connected
```

**Status**: ✅ RESOLVED

## Current System Status

### ✅ Working Components
- **User Authentication**: SQLite-based user management
- **Document Processing**: Multi-format text extraction
- **Policy Analysis**: NLP pipeline and classification
- **Chart Generation**: Plotly-based visualisations
- **Export System**: PDF, Word, and Excel generation
- **MongoDB Integration**: Robust connection handling
- **Admin Dashboard**: Full administrative functionality

### 🔧 Recently Fixed
- **PyMongo Compatibility**: Safe Collection object handling
- **Chart Rendering**: Proper Plotly integration
- **MongoDB Resilience**: Graceful connection failures
- **Template Rendering**: Correct data serialization

### 📋 Known Limitations
- **Browser Requirements**: JavaScript must be enabled for charts
- **MongoDB Dependency**: Required for full functionality (graceful fallback)
- **File Size**: Maximum 10MB per document
- **Processing Time**: Complex documents may take several minutes

## Common Error Messages and Solutions

### MongoDB Connection Errors

**Error**: `Connection refused` or `ServerSelectionTimeoutError`
```bash
# Solution 1: Start MongoDB service
brew services start mongodb/brew/mongodb-community

# Solution 2: Use Docker
docker run -d -p 27017:27017 --name mongodb-policycraft mongo:7

# Solution 3: Check if port is in use
lsof -i :27017
```

**Error**: `BadValue: Server fork+exec via --fork is incompatible with macOS`
```bash
# Solution: macOS doesn't support --fork, use background process
mongod --dbpath /opt/homebrew/var/mongodb --logpath /opt/homebrew/var/log/mongodb/mongo.log &
```

### Chart Display Issues

**Problem**: Charts not showing in browser
```bash
# Check browser console for JavaScript errors
# Verify Plotly is installed
pip install plotly

# Check application logs for chart generation
tail -f logs/application.log | grep -i chart
```

**Problem**: Export errors with charts
```bash
# Charts are now properly serialized for export
# Check if the issue persists after recent fixes
```

### Application Startup Issues

**Error**: `requirements.txt not found`
```bash
# Ensure you're in the correct directory
cd PolicyCraft
ls requirements.txt

# Run setup script from project root
./setup_new_dev.sh
```

**Error**: Virtual environment not activated
```bash
# Activate virtual environment
source venv/bin/activate

# Verify activation
which python
# Should show: .../venv/bin/python
```

## Performance Optimization

### MongoDB Performance
- **Connection Pooling**: Automatic connection management
- **Indexing**: Automatic index creation for common queries
- **Timeout Handling**: 5-second connection timeout prevents hanging

### Chart Generation
- **Lazy Loading**: Charts generated only when needed
- **Caching**: Chart data cached for repeated access
- **Error Recovery**: Graceful fallback when chart generation fails

### Memory Management
- **Streaming**: Large documents processed in chunks
- **Cleanup**: Automatic resource cleanup after processing
- **Monitoring**: Memory usage logged for debugging

## Debugging and Logging

### Application Logs
```bash
# View real-time logs
tail -f logs/application.log

# Filter by component
tail -f logs/application.log | grep -i "mongo\|chart\|analysis"

# Check for errors
tail -f logs/application.log | grep -i "error\|exception"
```

### MongoDB Logs
```bash
# macOS with Homebrew
tail -f /opt/homebrew/var/log/mongodb/mongo.log

# Docker
docker logs mongodb-policycraft

# System service
journalctl -u mongod -f
```

### Debug Mode
```bash
# Enable Flask debug mode
export FLASK_ENV=development
export FLASK_DEBUG=1

# Start with debug information
python app.py
```

## Getting Help

### Before Reporting Issues
1. **Check this guide** for known solutions
2. **Review application logs** for error details
3. **Verify system requirements** are met
4. **Test with minimal setup** to isolate problems

### Information to Include
- **Error message** (exact text)
- **Application logs** (relevant sections)
- **System information** (OS, Python version, MongoDB version)
- **Steps to reproduce** the issue
- **What you've already tried**

### Support Channels
- **Documentation**: Check this guide and other docs first
- **GitHub Issues**: For bug reports and feature requests
- **Logs Analysis**: Self-diagnosis using provided logging tools

---

**Note**: This guide is updated regularly as new issues are identified and resolved. Always check for the latest version when troubleshooting.
