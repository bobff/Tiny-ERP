#!/bin/sh
pid=`ps -aux | grep -v 'grep' | grep 'python manage.py runserver --settings=mysite.settings_dev 0.0.0.0:8000' | awk  '{print $2}' | awk 'NR==1'`
sudo kill $pid
python manage.py runserver --settings=mysite.settings_dev 0.0.0.0:8000
