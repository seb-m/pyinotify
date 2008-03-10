#!/bin/bash

for a in 1 2 3 4 5 6 7 8 9 10
do
  touch /tmp/test1234;
  echo -ne "42" > /tmp/test1234;
  rm -f /tmp/test1234;
done
