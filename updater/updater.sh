#!/bin/bash
cd $HOME/extemp/repo/updater
echo "dumping server database"
name=forensics-$(date +"%Y-%m-%d").sql
ssh extemp-update & ssh_pid=$!
sleep 100
mysqldump -u extemp --password="EwgEjDX289qyBs3" -h localhost -P 3310 --protocol=tcp --opt forensics > ${name}
kill -9 $ssh_pid
echo "importing new database"
mysql -u extemp --password="zhH/5]qAYTNNXgE" forensics < ${name}
echo "indexing"
sudo indexer --all --rotate
