#!/bin/bash

# Helper functions for working with AWS
# aws_ec2_list 						- List all instances and their current state
# aws_ec2_start instance-id 		- Start an existing instance by ID
# aws_ec2_stop instance-id 			- Stop a running instance by ID
# aws_ec2_create custom-instance-name - Creates a new instance with custom name. See and edit function definition before using this!
# aws_ec2_delete instance-id 		- Permanently delete instance by ID
# aws_ec2_terminate instance-id 	- Same as aws_ec2_delete

function check_number_of_args() {
	if [ $1 -ne $2 ]; then
		echo "$3" 1>&2
		return 1
	fi
}

function aws_ec2_list () {
	aws ec2 describe-instances | jq -r '.Reservations[].Instances[] | (.Tags[] | select (.Key == "Name")).Value, .InstanceType, .InstanceId, .State.Name' | awk '{ printf "| %-16s ", $0 }; NR%4==0 { printf "|\n" }'
}

function aws_ec2_start () {
	check_number_of_args $# 1 "Provide instance ID as argument!" || return 1

	(
		set -x

		aws ec2 start-instances --instance-ids $1 1> /dev/null
	)

	aws_ec2_list | grep --color=never $1
}

function aws_ec2_stop () {
	check_number_of_args $# 1 "Provide instance ID as argument!" || return 1

	(
		set -x

		aws ec2 stop-instances --instance-ids $1 1> /dev/null
	)

	aws_ec2_list | grep --color=never $1
}

function aws_ec2_create () {
	IMAGE_AMI_ID="ami-09e67e426f25ce0d7" # Ubuntu 20.04
	SECURITY_GROUP="sg-0e6739a61403cb89d" # Default or pick your own
	INSTANCE_TYPE="t2.micro"
	KEY_NAME="matyas-aws" # Name of the keypair you generated

	check_number_of_args $# 1 "Pick a name for this instance!" || return 1

	RAND_NAME_PART=`tr -dc A-Za-z0-9 </dev/urandom | head -c 4 ; echo ''`
	INSTANCE_NAME="$1-$RAND_NAME_PART"

	(
		set -x

		aws ec2 run-instances --image-id "$IMAGE_AMI_ID" --count 1 --instance-type "$INSTANCE_TYPE" --key-name "$KEY_NAME" --security-group-ids "$SECURITY_GROUP" --tag-specifications 'ResourceType=instance,Tags=[{Key="Name",Value='\""$INSTANCE_NAME"\"'}]' 1> /dev/null
	)

	aws_ec2_list | grep --color=never $INSTANCE_NAME
}

function aws_ec2_delete () {
	check_number_of_args $# 1 "Provide instance ID to terminate. This will PERMANENTLY delete the instance." || return 1

	(
		set -x

		aws ec2 terminate-instances --instance-ids $1 1> /dev/null
	)

	aws_ec2_list | grep --color=never $1

}

function aws_ec2_terminate () {
	aws_ec2_delete "$@"
}
