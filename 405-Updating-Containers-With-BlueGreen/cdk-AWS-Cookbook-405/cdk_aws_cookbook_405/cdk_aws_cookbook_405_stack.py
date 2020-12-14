from aws_cdk import (
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_s3 as s3,
    aws_ecr_assets as ecr_assets,
    aws_elasticloadbalancingv2 as alb,
    core,
)


class CdkAwsCookbook405Stack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ecr_asset_blue = ecr_assets.DockerImageAsset(
            self,
            'ecr_asset_blue',
            directory='DockerBlue',
        )

        ecr_asset_green = ecr_assets.DockerImageAsset(
            self,
            'ecr_asset_green',
            directory='DockerGreen',
        )

        # create VPC
        vpc = ec2.Vpc(
            self,
            'AWS-Cookbook-VPC'
        )

        albSecurityGroup = ec2.SecurityGroup(
            self,
            'albSecurityGroup',
            description='Security Group for the ALB',
            allow_all_outbound=True,
            vpc=vpc
        )

        albSecurityGroup.add_ingress_rule(
            peer=ec2.Peer.ipv4("0.0.0.0/0"),
            connection=ec2.Port.tcp(80),
            description='Allow HTTP from the world',
            remote_rule=False
        )

        albSecurityGroup.add_ingress_rule(
            peer=ec2.Peer.ipv4("0.0.0.0/0"),
            connection=ec2.Port.tcp(8080),
            description='Allow 8080 from the world',
            remote_rule=False
        )

        fargate_service_security_group = ec2.SecurityGroup(
            self,
            'fargate_service_security_group',
            description='Security Group for the Fargate Service',
            allow_all_outbound=True,
            vpc=vpc
        )

        fargate_service_security_group.connections.allow_from(
            albSecurityGroup, ec2.Port.tcp(80), "Ingress")

        # create ECS Cluster
        ecs_cluster = ecs.Cluster(
            self,
            'AWS-Cookbook-EcsCluster',
            cluster_name='awscookbook405',
            vpc=vpc
        )

        FargateTaskBlue = ecs.FargateTaskDefinition(
            self,
            'FargateTaskBlue',
            cpu=256,
            memory_limit_mib=512,
        )

        ContainerDefBlue = ecs.ContainerDefinition(
            self,
            'ContainerDefBlue',
            image=ecs.ContainerImage.from_docker_image_asset(ecr_asset_blue),
            task_definition=FargateTaskBlue,
        )

        ContainerDefBlue.add_port_mappings(
            ecs.PortMapping(
                container_port=80
            )
        )

        FargateTaskGreen = ecs.FargateTaskDefinition(
            self,
            'FargateTaskGreen',
            cpu=256,
            memory_limit_mib=512,
        )

        ContainerDefGreen = ecs.ContainerDefinition(
            self,
            'ContainerDefGreen',
            image=ecs.ContainerImage.from_docker_image_asset(ecr_asset_green),
            task_definition=FargateTaskGreen,
        )

        ContainerDefGreen.add_port_mappings(
            ecs.PortMapping(
                container_port=80
            )
        )

        FargateService = ecs.FargateService(
            self,
            'awscookbook405',
            cluster=ecs_cluster,
            task_definition=FargateTaskBlue,
            assign_public_ip=False,
            desired_count=2,
            enable_ecs_managed_tags=False,
            # health_check_grace_period=core.Duration.seconds(60),
            max_healthy_percent=100,
            min_healthy_percent=0,
            platform_version=ecs.FargatePlatformVersion('LATEST'),
            security_group=fargate_service_security_group,
            service_name='AWSCookbook405',
            deployment_controller=ecs.DeploymentController(
                type=ecs.DeploymentControllerType('CODE_DEPLOY')
            ),
            vpc_subnets=ec2.SubnetSelection(
                one_per_az=False,
                subnet_type=ec2.SubnetType('PRIVATE')
            )
        )

        lb = alb.ApplicationLoadBalancer(
            self,
            'LB',
            vpc=vpc,
            deletion_protection=False,
            http2_enabled=True,
            idle_timeout=core.Duration.seconds(60),
            internet_facing=True,
            ip_address_type=alb.IpAddressType('IPV4'),
            load_balancer_name='FargateServiceALB',
            security_group=albSecurityGroup,
            vpc_subnets=ec2.SubnetSelection(
                one_per_az=False,
                subnet_type=ec2.SubnetType('PUBLIC')
            )
        )

        DefaultTargetGroup = alb.ApplicationTargetGroup(
            self,
            "DefaultTargetGroup",
            port=80,
            vpc=vpc,
            target_group_name="DefaultTG",
            target_type=alb.TargetType('IP'),
        )

        listener80 = alb.ApplicationListener(
            self,
            'listener80',
            load_balancer=lb,
            open=False,
            port=80,
            protocol=alb.ApplicationProtocol('HTTP'),
            default_target_groups=[DefaultTargetGroup]
        )

        BlueTargetGroup = listener80.add_targets(
            'BlueTargetGroup',
            deregistration_delay=core.Duration.seconds(60),
            health_check=alb.HealthCheck(
                healthy_http_codes='200',
                healthy_threshold_count=2,
                interval=core.Duration.seconds(10),
                path='/',
                port='traffic-port',
                protocol=alb.Protocol('HTTP'),
                unhealthy_threshold_count=2
            ),
            host_header="*.*.*",
            port=80,
            priority=1,
            protocol=alb.ApplicationProtocol('HTTP'),
            target_group_name="BlueTG",
            targets=[FargateService]
        )

        listener8080 = alb.ApplicationListener(
            self,
            'listener8080',
            load_balancer=lb,
            open=False,
            port=8080,
            protocol=alb.ApplicationProtocol('HTTP'),
            default_target_groups=[BlueTargetGroup]
        )

        # create s3 bucket
        s3_Bucket = s3.Bucket(
            self,
            "AWS-Cookbook-Recipe405",
            removal_policy=core.RemovalPolicy.DESTROY
        )

        # outputs

        core.CfnOutput(
            self,
            'BlueImage',
            value=ecr_asset_blue.image_uri
        )

        core.CfnOutput(
            self,
            'GreenImage',
            value=ecr_asset_green.image_uri
        )

        core.CfnOutput(
            self,
            'VPCId',
            value=vpc.vpc_id
        )

        core.CfnOutput(
            self,
            'LoadBalancerDNS',
            value=lb.load_balancer_dns_name
        )

        core.CfnOutput(
            self,
            'ECSClusterName',
            value=ecs_cluster.cluster_name
        )

        public_subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC)

        core.CfnOutput(
            self,
            'VPCPublicSubnets',
            value=', '.join(map(str, public_subnets.subnet_ids))
        )

        core.CfnOutput(
            self,
            'VPCDefaultSecurityGroup',
            value=vpc.vpc_default_security_group
        )

        core.CfnOutput(
            self,
            'S3BucketName',
            value=s3_Bucket.bucket_name
        )

        core.CfnOutput(
            self,
            'BlueTargetGroupName',
            value=BlueTargetGroup.target_group_arn
        )

        core.CfnOutput(
            self,
            'ProdListenerArn',
            value=listener80.listener_arn
        )

        core.CfnOutput(
            self,
            'TestListenerArn',
            value=listener8080.listener_arn
        )

        core.CfnOutput(
            self,
            'DefaultTargetGroupArn',
            value=DefaultTargetGroup.target_group_arn
        )

        core.CfnOutput(
            self,
            'FargateTaskBlueArn',
            value=FargateTaskBlue.task_definition_arn
        )

        core.CfnOutput(
            self,
            'FargateTaskGreenArn',
            value=FargateTaskGreen.task_definition_arn
        )
