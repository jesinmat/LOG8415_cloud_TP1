# Temporary branch with my tools

-   aws-script.py - use to work with AWS easily. Install `boto3` for Python 3 and enter credentials into ~/.aws/credentials
	- Simple REPL interface. Run the file with python3 and it will show usage info.
    - You **MUST** edit `create` and `ssh` functions to use your own values (key and security group) and commands (ssh), I have it set up for my machine.2
    - You can then use `c custom-instance-name --userScript=flask_deploy.sh` to install everything and deploy flask app on port 80.

- aws-skripty.sh - bash version of some basic AWS commands. Do not use.

# Docker

To build and run docker loadtesting and metrics reporting, do the following:

To create the image (once is enough):
```
cd docker-loadtester
./buildDockerImage.sh
```

To run the loadtest and get metrics:

- make sure you have working aws credentials in ~/.aws/credentials

- in one terminal window:

    ```
    python3 load_balancer.py
    ```

- in another terminal:

    Wait for load balancer to finish setting up and copy the loadbalancer URL
    ```
    export AWS_URL='http://load-balancer.....aws.com' # set variable, don't forget to add the http://
    cd docker-loadtester
    ./runDockerContainer.sh
    ```

- When docker exits, results will appear inside `output` directory. You can return to the first terminal and terminate load balancer.

