#!/bin/sh

sed -i.bak '1,2d' ./src/amps/amps.py
pdoc3 --html ./src/amps --output-dir ./docs --force
mv ./docs/amps/* ./docs
rm -rf ./docs/amps
echo 'from erlport.erlang import cast, call\nfrom erlport.erlterms import Atom' | cat - ./src/amps/amps.py > temp && mv temp ./src/amps/amps.py
rm ./src/amps/amps.py.bak

