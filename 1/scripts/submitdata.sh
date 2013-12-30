# !/bin/sh

cd $1
for f in part-r-*;
do
    curl --verbose --user-agent "Mozilla/5.0 (X11; Uuntu; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0" -F "myfile=@$f" "http://mozillaup.sinaapp.com/?context="
    echo "Uploaded $f, and sleep 30s"
    sleep 30
done

