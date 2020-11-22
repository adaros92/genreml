# Run unit tests; coverage report will be generated as .coverage
bash install.sh
{
  pytest --cov=genreml ./test
} ||
{
  pip3 install pytest
  python3 -m pytest --cov=genreml ./test
} ||
{
  pip install pytest
  python -m pytest --cov=genreml ./test
}
rm -rf ./test_dir* ./feature_data_* .pytest_cache *.egg*