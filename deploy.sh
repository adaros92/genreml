{
  python setup.py test && python setup.py sdist bdist_wheel
} ||
{
  python3 setup.py test && python3 setup.py sdist bdist_wheel
}
# The following assumes you have
twine upload dist/*
rm -rf ./test_dir* ./feature_data_* .pytest_cache *.egg*
