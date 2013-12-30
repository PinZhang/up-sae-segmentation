# !/bin/sh

SRCDIR=$1
DESDIR=$2
for dir in $(find $SRCDIR -type d);
do
    echo $(basename $dir)
    find $dir -type f | while read file; do cat $file >> $DESDIR/$(basename $dir)_output.txt; done;
done
