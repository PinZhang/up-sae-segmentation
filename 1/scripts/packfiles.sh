# !/bin/sh

rm ./output.txt
echo "Merge all fragments"
find $1 -type f | while read file; do cat $file >> ./output.txt; done;
echo "Pack merged file"
tar -cjvf seg-result.tar.bz2 output.txt
