# First try with python
{
  pip install -e .
} ||
{ # If python fails, try with python3
  pip3 install -e .
}
{
  source ~/.zprofile
} ||
{
 source ~/.bash_profile
}
rm -rf ./test_dir*
