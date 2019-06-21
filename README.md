# Maniple 

Maniple automates packaging and deploying AWS Lambda functions when working with Terraform. 

Only supports javascript and python.

### Basic file structure

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

### Basic configuration

Set your config to the name of the lambda function currently being worked on.

    $ maniple config -l lambda-function-name


### Deploying a function from scratch

Lambda expects your code to already be uploaded to a S3 bucket when the function is created.

In your terraform directory.

    $ maniple pack -c -up
    $ terraform apply

### Working with a function that is already created

Download and package all requisite packages and deploy:

    $ maniple deploy

Only update your script (ie don't re-download packages):

     $ maniple deploy -u


### Updating multiple functions in the same terraform file

    $ maniple deploy -a

Check --help for each command to see more options.

### Install

Download Maniple and, in its downloaded directory, run:

    $ pip install --editable .




