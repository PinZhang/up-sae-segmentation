# !/bin/sh

USER=yyl53lxjwz
KEY=ymlh355zw1l45ijy4z4khz5xz0hwmhlx3ilwlh4h
echo "delete container mozillaup"
swift -A https://auth.sinas3.com/v1.0 -U $USER -K $KEY delete mozillaup
