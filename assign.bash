#!/bin/bash

set -e

EMAIL=$1
DIR="./skiff_files/apps/pawls/sections-annotation"

for SHA in $(ls $DIR | egrep '^.{40,}$'); do
  pawls assign $DIR $EMAIL $SHA
done
