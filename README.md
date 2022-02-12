# Snowcone-Greengrass
AWS IoT Greengrass allows you to build, deploy, and manage device software to the Edge at-scale. In this demo, we show how IoT Greengrass manages an AI/ML model on Snowcone. Our AI/ML model detacts faces and draws rectangles around the eyes and face.

Requirements
AWS Snowcone
IP camera capable of outputting an MJPEG stream

Assumptions
1. The Snowcone was ordered with the AWS IoT Greengrass validated AMI (amzn2-ami-snow-family-hvm-2.0.20210219.0-x86_64-gp2-b7e7f8d2-1b9e-4774-a374-120e0cd85d5a).
2. The reader is familar with OpsHub and the SnowballEdge client.
3. The SnowballEdge client has been configured with the appropriate Snowcone credentials.


Snowcone setup
1. Deploy an Amazon Linux 2 instance. The instance type should be snc1.medium. 
   (optional)
   If you are setting up a long term demo, you can setup your instance to startup automatically after unlocking. Use the following autostart configuration.
   aws ec2 create-launch-template --launch-template-name al2-template2 --version-description version2 --launch-template-data "{\"ImageId\":\"s.ami-8144e2b13711e662b\",\"InstanceType\":\"sbe-c.large\",\"KeyName\":\"markngykp\",\"SecurityGroupIds\":[\"s.sg-8f511ebd4681ca816\"],\"EbsOptimized\":true}" --endpoint http://192.168.26.89:8008 --profile sbe89 --region snowballedge
   snowballEdge create-autostart-configuration --physical-connector-type RJ45 --ip-address-assignment DHCP --launch-template-id s.lt-81d2c737e1adde32f --endpoint https://192.168.26.89 --profile sbe89
2. sdlkfj
