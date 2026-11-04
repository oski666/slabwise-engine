#!/bin/sh
# Anteprima del sito Slabwise su Mac/Linux: ricostruisce la pagina e la apre nel browser.
cd "$(dirname "$0")" && python3 prototype/v7/build.py && (open prototype/v7/slabwise.html 2>/dev/null || xdg-open prototype/v7/slabwise.html)
