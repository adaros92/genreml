# First try with python
{
  pip uninstall genreml
} ||
{ # If python fails, try with python3
  pip3 uninstall genreml
}
rm -rf ./.eggs ./build ./dist ./.pytest_cache ./.coverage ./test_dir*
