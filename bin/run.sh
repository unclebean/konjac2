 #!/bin/bash

echo "run command {$1} ..."
  
PIDFILE=app.pid
case $1 in
    start)
        pwd
        # Launch your program as a detached process
        exec poetry run gunicorn konjac2.main:app --workers 1 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:5555
        # Get its PID and store it
        echo $! > ${PIDFILE}
    ;;
    stop)
        pwd
        # Launch your program as a detached process
        kill -12 `cat ${PIDFILE}`
        # Now that it’s killed, don’t forget to remove the PID file
        rm ${PIDFILE}
    ;;
    *)
esac
exit 0
