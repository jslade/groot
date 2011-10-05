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

echo $marker

exit $ret
