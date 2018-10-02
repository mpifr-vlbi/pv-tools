host=`hostname -s`
echo $host
mv /home/oper/shared/logs/vv_${host}_eth3.log /home/oper/shared/logs/vv_${host}_eth3.log.bak

mv /home/oper/shared/logs/vv_${host}_eth5.log /home/oper/shared/logs/vv_${host}_eth5.log.bak

while sleep 60; do
	/home/oper/bin/vv -i eth3 -p 4001 >> /home/oper/shared/logs/vv_${host}_eth3.log
	/home/oper/bin/vv -i eth5 -p 4001 >> /home/oper/shared/logs/vv_${host}_eth5.log
done
