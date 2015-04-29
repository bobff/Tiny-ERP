#!/bin/sh
pid=`ps -aux | grep -v 'grep' | grep 'uwsgi erp.xml --plugin python' | awk  '{print $2}' | awk 'NR==1'`
if [ -z $pid ]; then
echo ' '
else
echo "kill $pid"
sudo kill $pid
fi
uwsgi erp.xml --plugin python
