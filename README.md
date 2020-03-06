# Electives recommendation system
A platform to aid students in choosing university electives. Allows multiple universities, students and tutors to be registered in the system. Students can rate courses they have enrolled in, allowing recommendations to be generated based on similarities between students' ratings. These recommendations are generated using latent factors, learnt via gradient descent on past course ratings. 

## Installing dependencies
This program is written in Python 3.7. Please use [pip](https://pip.pypa.io/en/stable/) package manager to install the necessary dependencies (it is recommended to install them in a virtual environment like venv).


Installation using pip:
```bash
cd [project_directory]
pip install -r requirements.txt
```

## Sample usage
A sample program is provided in demo.py