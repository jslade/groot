#!/bin/sh
# This wrapper script is used by git.py to execute commands when running
# with a pty. It outputs a special output marker after the command is
# done so git.py can correctly detect the end of output.

marker=$1
shift

cmd=$1
shift

$cmd ${1+"$@"}
ret=$?

trap continue PIPE # reduce broken pipe warnings

echo $marker:$ret
for i in 1 2 3 4 5; do
    echo $marker:$ret
    sleep 1
done

exit $ret
