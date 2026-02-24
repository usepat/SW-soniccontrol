
# Create Test Reports with allure

Allure can be installed with the node package manager (npm) via:
```
sudo npm -g install allure
```

The test reports are automatically created when running pytest in the directory *output/allure*. This is done by injecting `--alluredir=path` option in *pyproject.toml*.

To create and open the allure report in the browser execute *allure serve*.
