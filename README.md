# CS467-Project
Repo for the CS467 captstone project

### Contributing
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
