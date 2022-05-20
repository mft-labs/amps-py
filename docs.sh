#!/bin/sh
rm -rf ./docs/*.html
sed -i -e  '1,2d' ./src/amps/__init__.py
pdoc3 --html ./src/amps --output-dir ./docs --force --template-dir ./templates
mv ./docs/amps/* ./docs
rm -rf ./docs/amps
echo 'from erlport.erlang import cast, call\nfrom erlport.erlterms import Atom' | cat - ./src/amps/__init__.py > temp && mv temp ./src/amps/__init__.py

