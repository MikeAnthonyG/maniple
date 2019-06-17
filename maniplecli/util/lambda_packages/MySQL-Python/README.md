# MySQL-Python

Built from MySQL-Python 1.2.5 from pip and MySQL from yum on EC2 Linux.

Build instructions [via Sean Hull](http://www.iheavy.com/2016/02/14/getting-errors-building-amazon-lambda-python-functions-help-howto/):

- virtualenv test
- source proj/bin/activate
- sudo yum groupinstall 'Development Tools'
- sudo yum install mysql
- sudo yum install mysql-devel
- pip install MySQL-python
- mv proj/lib/python2.7/site-packages/* proj/
- mv proj/lib64/python2.7/site-packages/* proj/
