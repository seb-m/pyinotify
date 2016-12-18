#!/bin/bash

## I recommend that you start with a clean test folder,
## but I wouldn't want someone to run this accidentally on something else.
#rm -rf test

mkdir -p test/rsync_to_here
mkdir -p test/src

for i in $(seq 1 10); do touch test/src/file${i}.raw; done
touch test/src/ignored_file.txt

#Fire up the autocruncher in the background:
./rsync_processing_pool.py &
AUTOCRUNCHER_PID=$!
#Wait for it to boot
sleep 1


#Test that errors get properly logged if something isn't right:
#Block output directory creation by placing a file of the same name:
echo "We expect a failure here:"
touch test/output

#Now try rsync (this will fail and log errors, but won't crash the autocruncher)
#(NB continued operation can be crucial, even if one of your processing ops fails!)
rsync test/src/file1.raw test/rsync_to_here
#Wait for the processes to catch up
sleep 1

echo "Now we remove the blocking file and try again - the same python daemon keeps on watching."
rm test/rsync_to_here/*
rm test/output
rsync test/src/* test/rsync_to_here


#Wait till all the processing has completed, then close down the autocruncher:
echo "Waiting for all processes to complete..."
sleep 4
kill $AUTOCRUNCHER_PID
echo "Process has been killed, why not check the logs?"
