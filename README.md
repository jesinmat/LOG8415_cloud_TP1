# LOG8415_cloud_TP1

Project for the Log8415 Cloud Computing course, 2021.

Authors: Pierre Ballif, Matyáš Ješina, Jakub Profota

## Running the whole project

- Copy the script.sh file into any folder.
- In the same folder, create a file named 'keypair-name' (with no extension) which contains the name of your key pair. For example, if your key is called `my_secret_key` and situated in `/path/to/my_secret_key.pem`, you will have to put `my_secret_key` into keypair-name. Do **not** put a newline at the end of the file.
- Run `script.sh`

# Developer part

**UPDATE `constant.py` FILE BEFORE USAGE**

Make sure you have valid credentials in `~/.aws/credentials`

-   aws-script.py - use to work with AWS EC2 easily.
	- Simple REPL interface. Run the file with python3 and it will show usage info.

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
