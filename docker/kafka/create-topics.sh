#!/usr/bin/env bash
set -e
sleep 20
for topic in signals scores mockups listings feedback; do
  kafka-topics.sh --bootstrap-server kafka:9092 --create --if-not-exists --topic "$topic"
done
