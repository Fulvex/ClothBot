#!/bin/bash

echo "Loading"
sleep 5
echo "Executing"

cd ~/ClothBot

/venv/bin/python -u -m app.py

echo "Done Executing"
