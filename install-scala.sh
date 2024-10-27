#!/bin/bash

# Determine system architecture
ARCH=$(uname -m)

# Download and set up Coursier based on the architecture
if [[ "$ARCH" == "x86_64" ]]; then
    echo "Detected x86_64 architecture. Downloading for x86_64."
    curl -fL https://github.com/coursier/coursier/releases/latest/download/cs-x86_64-pc-linux.gz | gzip -d > cs
elif [[ "$ARCH" == "aarch64" ]]; then
    echo "Detected ARM architecture. Downloading for ARM."
    curl -fL https://github.com/VirtusLab/coursier-m1/releases/latest/download/cs-aarch64-pc-linux.gz | gzip -d > cs
else
    echo "Unsupported architecture: $ARCH"
    echo "Exiting"
    exit 1
fi

# Make the downloaded cs command executable
chmod +x cs
echo "Setting up cs command with Scala."
yes | ./cs setup

# Check if the Scala command is available
echo "Checking if the Scala command is available"
if command -v scala &> /dev/null
then
    echo "Scala is installed and available."
else
    echo "Scala is not installed or not in the PATH."

    # If cs has installed Scala but PATH is missing, add it to the PATH
    SCALA_PATH="$HOME/.local/share/coursier/bin"  # Typical installation path for coursier
    if [[ -d "$SCALA_PATH" ]]; then
        export PATH="$SCALA_PATH:$PATH"
        echo "Added Scala to PATH."
    else
        echo "Scala installation path not found."
    fi
fi
