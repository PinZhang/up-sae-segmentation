# !/bin/sh

cd $1
USER=yyl53lxjwz
KEY=ymlh355zw1l45ijy4z4khz5xz0hwmhlx3ilwlh4h
swift -A https://auth.sinas3.com/v1.0 -U $USER -K $KEY list mozillaup | while read -r FILE
do
    echo "Download file $FILE"
    swift -A https://auth.sinas3.com/v1.0 -U $USER -K $KEY download mozillaup $FILE
done
