#!/bin/sh

#CMD=odatse-STR
CMD="python3 ../../../src/main.py"

export PYTHONUNBUFFERED=1

sh prepare.sh

../../bin/bulk.exe

time $CMD input.toml

result=output/res.txt
reference=ref.txt

echo diff $result $reference
res=0
diff $result $reference || res=$?
if [ $res -eq 0 ]; then
  echo TEST PASS
  true
else
  echo TEST FAILED: $result and $reference differ
  false
fi

