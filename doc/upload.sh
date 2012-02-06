#! /bin/bash

rsync -avP -e ssh _build/html/* mcfletch,ttfquery@web.sourceforge.net:htdocs/
