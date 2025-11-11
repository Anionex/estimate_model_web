SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
cd "$SCRIPT_DIR"

echo "--- Stopping existing server on port 5000 ---"
sudo kill -9 $(sudo lsof -t -i :5000)

echo "--- Applying database migrations ---"
export FLASK_APP=backend.py
flask db upgrade

echo "--- Starting Gunicorn server ---"
python -m gunicorn --capture-output -w 4 -t 1500 backend:app --bind 127.0.0.1:5000 --daemon --access-logfile access.log --error-logfile error.log
lsof -t -i :5000
tail -f -n 50 error.log access.log