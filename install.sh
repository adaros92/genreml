# First try with python
{
  python setup.py test && pip install -e .
} ||
{ # If python fails, try with python3
  python3 setup.py test && pip3 install -e .
}
source ~/.bash_profile
rm -rf ./test_dir*
