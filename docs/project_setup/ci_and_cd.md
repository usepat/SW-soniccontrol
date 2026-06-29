@defgroup CIandCD
@ingroup ProjectSetup
@addtogroup CIandCD
@{

# Continuous Integration and Continuous Deployment {#CIandCD}

> Attention: CI and CD is not actively developed anymore, because we ran into issues with github storage limits and run time limits. Anyways we still have tests, we run them manually.

Continuous integration and continuous deployment means that you automate the testing and building of your software. Automation is important because it enforces those processes and ensures that they always run in the same manner.

## Github Actions

For CI and CD we use [Github Actions](https://github.com/features/actions).
In workflow files inside *.github/workflows* we can define different processes to run. 
For that [YAML](https://yaml.org/spec/1.2.2/) is used as configuration language.
In short we can define tasks that run on [containers](https://www.docker.com/resources/what-container/) inside a server on github.
Those tasks define a serious of steps to execute, for example bash commands.
We can clone repositories with the `actions/checkout@v3` action, then set up the environment, download and upload artifacts and much more.  
Artifacts are files that we can upload, download with `actions/upload-artifact@v4`, `actions/download-artifact@v4`.  
Actions are reusable scripts provided by other contributors on github. There exists a full library of them and you can also write them by your own.

Also an important note is that you can specify when a workflow triggers a run. You can also start them manually by specifying:
```yaml
on:
  workflow_dispatch:
```
and then pressing a *run workflow button* on github.

@}