{
  python setup.py sdist bdist_wheel
} ||
{
  python3 setup.py sdist bdist_wheel
}
# The following assumes you have
twine upload dist/*