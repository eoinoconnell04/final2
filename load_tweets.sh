#!/bin/sh


echo 'load tweets, users, and urls'
python3 load_tweets.py --db=postgresql://postgres:pass@localhost:28922
