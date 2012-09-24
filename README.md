About Autobuild
===========

This Autobuild System is designed to undertake the building and testing 
process automatically. It depends on the following packages:

+ Python2.7
+ Git
+ Bash


Deployment
============

Use uCore for example. 

1. First, you must create a working directory.

*mkdir work*

*cd work*

2. Then, download the git-build.py from my [Repo](https://github.com/chyh1990/autobuild_tester),
put it into *work*.

3. Clone your Repo which you wanted to be built automatically.
Make sure using the *Readonly* URL.

*git clone https://github.com/chyh1990/autobuild_tester*

4. Configure the git-build.py, see the following section.

5. Setup the Service Hook in Github.

Click Admin -> Service Hooks -> WebHook URLs.


Configuration
===========
To make it simple, all options are in gitbuild_config.py, and no extra configure files.

+ PORT_NUMBER: listening port of the HTTP server
+ CLIENT_IPS:  only POST requests from these hosts will trigger the auto-build.
+ REPO_NAME:   the name of your target Repo
+ LOCAL_REPO:  the path of its local clone


Testing
===========
Run the python server:

*nohup python git-build.py*

Then open the web browser, goto 
http://127.0.0.1:PORT_NUMBER/

You should be able to see the start page.

When someone pulls commits to the Repo, it will trigger the auto-building and auto-testing.
This means a Git fetch action and then the *autobuild.sh* and *autotest.sh* will be run.
You should make sure these two scripts are placed in the root of your target Repo properly.

After you pull your commits to Github, Github will inform our HTTP server.

*NOTE: Only commits whose message starts with AUTOTEST will trigger a rebuild and re-test.*

Example:

git commit -am"AUTOTEST blabla"

git pull


