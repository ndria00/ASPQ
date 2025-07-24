# Casper
In order to run Casper please clone this repository and then follow the instructions.

## Install
The following commands run from the root of the repository wil build and isntall the Casper solver in a Python virtual environment using the venv virtual environment manager

```
python3 -m venv venv
source venv/bin/activate
pip install .
```
## Execute
usage: Casper [-h] --problem PROBLEM [--instance INSTANCE] [--debug] [--constraint] [--relaxed] [-n N]

A native solver based on CEGAR for 2-ASP(Q)

options:
  -h, --help           show this help message and exit
  --problem PROBLEM    path to problem file
  --instance INSTANCE  path to instance file
  --debug              enable debug
  --constraint         enable constraint print of models
  --relaxed            pick first model as a model of the union of relaxed programs
  -n N                 number of q-answer sets to compute (if zero enumerate)

The --instance option can be used to make transformations more efficient

The --relaxed option may be used for avoiding to pick the first model at random (it tries to take an answer set of the first program for which an answer set of the second exists)

The --constraint option can be used to print each quantified answer set as a set of constraints. The output can be used to verify the correctness of computed models.

By default the solver does not used relaxation, computes only one ansswer set and expect the instance of the problem to be inside the problem file.