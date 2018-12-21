#!/usr/bin/env bash

python cloudiot_http_example.py \
    --registry_id=inventory1 \
    --cloud_region=europe-west1 \
    --project_id=wassermat \
    --device_id=raspi1 \
    --message_type=event \
    --algorithm=RS256 \
    --private_key_file=resources/rsa_private.pem
