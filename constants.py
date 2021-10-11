import os

def KEYPAIR_NAME():
	return open('~/.aws/keypair-name').read()

def SECURITY_GROUP():
	return input('Please enter a security group name.')

IMAGE_ID = 'ami-09e67e426f25ce0d7'