# Temporary branch with my tools

-   aws-script.py - use to work with AWS easily. Install `boto3` for Python 3 and enter credentials into ~/.aws/credentials
	- Simple REPL interface. Run the file with python3 and it will show usage info.
    - You **MUST** edit `create` and `ssh` functions to use your own values (key and security group) and commands (ssh), I have it set up for my machine.
    - You can then use `c custom-instance-name --userScript=flask_deploy.sh` to install everything and deploy flask app on port 80.

- aws-skripty.sh - bash version of some basic AWS commands. Do not use.