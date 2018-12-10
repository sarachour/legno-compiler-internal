

for pid in $(ps -eo pid,command | grep moira | grep -o "^ [0-9]*") 
do
	echo "killing $pid"
	kill -9 $pid
done

