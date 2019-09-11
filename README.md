# Maniple 

A framework for working with AWS Lambda functions and Terraform.

Currently, supports javascript and python.

### Standard file structure

```
---TerraformDirectory
	|---main.tf
	|---package.json
	|---src
		|---app.js
	|---tests
		|---test-app.js
```

```
---TerraformDirectory
	|---main.tf
	|---requirements.txt
	|---src
		|---app.py
	|---tests
		|---test_app.py
```

Working with multiple lambda functions inside a `main.tf` file requires each resource to either have a directory containing it's code or a single file.

```
---TerraformDirectory
	|---main.tf
	|---lambda_fn_one.txt  # requirements for lambda_fn_one
	|---lambda_fn_two.txt  # requirements for lambda_fn_two
	|---lambda_fn_one.py   # script for lambda_fn_one
	|---lambda_fn_two  # src would also work here
		|---lambda_fn_two.py  # script for lambda_fn_two
		|---lambda_fn_two_helper.py  # will be included in deployment package for lambda_fn_two
	|---tests
		|---test_lambda_fn_one.py
		|---test_lambda_fn_two.py
```

### Bare minimum file structure

Python
```
---TerraformDirectory
     |---script.py
     |---requirements.txt
     |---main.tf
```

Javascript
```
---TerraformDirectory
     |---script.js
     |---package.json
     |---main.tf
```

## Commands

### new
Creates the basic file structure for a lambda function including a src and tests folder.

	$ maniple new [TEMPLATE] [NAME]
	
Creating a new JS function:

	$ maniple new jsapp your-name-here
	
Creating a new python function:

	$ maniple new pyapp your-name-here
	
### deploy
Deploys functions to the cloud.

Create deployment package, upload package, and notify AWS of changes to the function.

	$ maniple deploy
	
Create a new lambda function and deploy on AWS (will run `terraform apply`).

	$ maniple deploy -n
	
Update the code of a pre-existing function.

	$ maniple deploy -u
	
Deploy multiple Lambda functions from a single main.tf file.

	$ maniple deploy -a
	
### pack
Offers more fine-tuned ways to create and update functions.

Create deployment package.

	$ maniple pack -c

Update deployment package.

	$ maniple pack -us

Upload a deployment package.

	$ maniple pack -up
	
Notify AWS of changes to a function's code.

	$ maniple pack -uf
	
### test
Runs test scripts located in the `tests` folder. This is useful for using the Python unittest package without creating a `__init__.py` file.

	$ maniple test
	
### config
Manipulate settings that override the default values loaded by maniple. Use the --help flag to see all settings that can be changed.

It is sometimes required to tell maniple which lambda function you are working with (e.g. a terraform file that includes multiple aws_lambda_function resources), setting the name of the function will isolate changes to only that resource.

	$ maniple config -n your-lambda-app-name

Load settings for a function

	$ maniple config -load

Get your current settings

	$ maniple config -g
	
Clear your current settings

	$ maniple config -c
	


## Other functionality
More command options can be viewed with:

	$ maniple [COMMAND] --help

Contains an extensive library of python packages that require binaries to run on AWS Linux. Maniple will prompt users if one of their packages can be replaced.
