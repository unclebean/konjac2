 #!/bin/bash

echo "run command {$1} ..."
  
PIDFILE=app.pid
case $1 in
    start)
        pwd
        # Launch your program as a detached process
        poetry shell
        uvicorn konjac2.main:app --host 0.0.0.0 --port 5555 2>/dev/null &
        # Get its PID and store it
        echo $! > ${PIDFILE}
    ;;
    stop)
        cd "$(dirname "${BASH_SOURCE[0]}")"
        pwd
        # Launch your program as a detached process
        kill -15 `cat ${PIDFILE}`
        # Now that it’s killed, don’t forget to remove the PID file
        rm ${PIDFILE}
    ;;
    *)
esac
exit 0
