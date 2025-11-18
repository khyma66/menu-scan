#!/bin/bash
export JAVA_HOME=/Applications/Android\ Studio.app/Contents/jbr/Contents/Home
export ANDROID_HOME=/Users/mohanakrishnanarsupalli/Library/Android/sdk
export PATH="$JAVA_HOME/bin:$PATH"
unset JAVA_TOOL_OPTIONS
./gradlew assembleDebug --no-daemon
