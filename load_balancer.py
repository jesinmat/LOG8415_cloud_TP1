def create_target_group(group_name : str, client):
    return client.create_target_group(
        Name=group_name,
        Protocol='HTTP',
        ProtocolVersion='HTTP1',
        Port=80,
        VpcId='vpc-073024149411a4a5a',
        HealthCheckEnabled=True,
        HealthCheckPath=f'/{group_name}',
        TargetType='instance',
        Tags=[
            {
                'Key': 'Name',
                'Value': f'target-group-{group_name}'
            },
        ]
    )