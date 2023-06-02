gunicorn --bind 127.0.0.1:5000 app:app & APP_PID=$!
sleep 5
echo start app
python3 app.py
python3 etst.py
sleep 5
echo $APP_PID
kill -TERM $APP_PID

if [ $EXIT_CODE -ne 0 ]; then
 echo "Error occurred: Exit code $EXIT_CODE"
fi

exit 0
