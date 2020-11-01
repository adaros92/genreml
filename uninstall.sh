# First try with python
{
  pip uninstall genreml
} ||
{ # If python fails, try with python3
  pip3 uninstall genreml
}
rm -rf ./src/*.egg* ./*.egg* ./build ./dist