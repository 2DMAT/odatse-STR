#!/bin/sh

sh prepare.sh

./bulk.exe

time mpiexec --oversubscribe -np 4 odatse-STR input.toml

echo diff output/fx.txt ref.txt
res=0
diff output/fx.txt ref.txt || res=$?
if [ $res -eq 0 ]; then
  echo TEST PASS
  true
else
  echo TEST FAILED: fx.txt and ref.txt differ
  false
fi

