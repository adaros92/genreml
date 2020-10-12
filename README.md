# CS467-Project
Repo for the CS467 capstone project

### Contributing

##### Git
The usual flow will be as follows.

1. Clone the repo
```
git clone git@github.com:adaros92/CS467-Project.git
```
2. Create new feature branch as feature/[name]
```
git checkout main
git pull
git checkout -b feature/initial-structure
```
3. Add code/make changes in feature branch
4. Commit to remote
```
git add .
git commit -m "Add initial structure to repository and contributing section to readme.md"
git push origin feature/initial-structure
```
5. Submit a pull request at https://github.com/adaros92/CS467-Project/pulls from your feature branch to the main branch
6. Resolve any comments locally and push a new revision to be reviewed
7. Solve any merge conflicts and merge the pull request

Useful git commands and references.

* Display available branches `git branch`
* Squashing commits into one for cleanliness https://gist.github.com/patik/b8a9dc5cd356f9f6f980
* Merge branch 
```
git checkout main
git merge other-branch
```
* Gitflow documentation https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow

##### Python Environment and Style
It's recommended to use the Pycharm IDE for making contributions. You can get it for free here: https://www.jetbrains.com/pycharm/. This will help you catch style and syntax issues early. 

We will try to follow PEP 8 whenever possible as documented here: https://www.python.org/dev/peps/pep-0008/. If you use Pycharm then you won't need to read this because it will highlight issues for you :). 

### Web-app Development
The web-app portion of the project will be stored in src/webapp. It will follow a typical Flask directory structure as documented in https://flask.palletsprojects.com/en/1.1.x/patterns/packages/. The instructions below assume you're working on a Unix environment.

To run a local server for testing do the following.

1. Create virtual environment in the top-level CS467-Project directory if not already available
```
python3 -m venv webapp-env
```
2. Activate that environment or the one that's available and verify that your terminal displays the name of the environment in between parentheses before the cursor
```
source webapp-env/bin/activate
```
3. Go into src and run shell script, which will install Flask and the local app
```
cd src && bash run_webapp.sh
```
4. Verify that terminal says app is running on http://127.0.0.1:5000/
5. Travel to http://127.0.0.1:5000/ or http://localhost:5000/ in the browser to view
6. Terminate Flask server by hitting Ctrl + C
7. Deactivate the virtual environment
```
deactivate
```
8. Delete the virtual environment if you want or leave it for reuse later
```
cd .. && rm -rf webapp-env
```

To deploy app to production.

TBU

### Model Development
TBU
