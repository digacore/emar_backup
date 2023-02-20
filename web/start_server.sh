#!/usr/bin/env bash
echo Run db upgrade
flask db upgrade
echo Run app
gunicorn -w 4 -b 0.0.0.0:5000 "wsgi:app"
