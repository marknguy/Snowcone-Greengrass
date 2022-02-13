# Snowcone-Greengrass
AWS IoT Greengrass allows you to build, deploy, and manage device software to the Edge at-scale. In this demo, we show how IoT Greengrass manages an AI/ML model on Snowcone. Our AI/ML model detacts faces and draws rectangles around the eyes and face.

###### Requirements
AWS Snowcone
IP camera capable of outputting an MJPEG stream

###### Assumptions
1. The Snowcone was ordered with the AWS IoT Greengrass validated AMI (amzn2-ami-snow-family-hvm-2.0.20210219.0-x86_64-gp2-b7e7f8d2-1b9e-4774-a374-120e0cd85d5a).
2. Familar with OpsHub and the SnowballEdge client. Both are installed on the user's computer. 
3. The SnowballEdge client has been configured with a profile using the appropriate Snowcone credentials.


###### Snowcone setup
1. Deploy an Amazon Linux 2 instance. The instance type should be snc1.medium. 

     (optional - requires AWS cli for the `aws ec2 ...` command)
   
      If you are setting up a long term demo, you can setup your instance to startup automatically after unlocking. The following autostart configuration sample works for Windows clients. Create a key pair in Opshub first if you don't already have one.
      First, create the launch template using aws cli. Make sure you replace `<ssh_key_name>` with your ssh key. Make sure you replace `<image_id>` with the image ID of your Amazon Linux 2 image. You can find the image ID using the command `aws ec2 describe-instances --endpoint http://192.168.26.89:8008 --profile snc89 --region snow`. It will look something like this: `s.ami-8144e2b13711e662b`. The endpoint is the IP address of your snowcone.
      ```
      aws ec2 create-launch-template --launch-template-name al2-template --version-description version1 --launch-template-data "{\"ImageId\":\"<image_id>\",\"InstanceType\":\"snc1.medium\",\"KeyName>\":\"<ssh_key_name>\"}" --endpoint http://192.168.26.89:8008 --profile snc89 --region snow
      ```
      Next, create the autostart configuration. Use the launch template ID from the previous command.
      ```
      snowballEdge create-autostart-configuration --physical-connector-type RJ45 --ip-address-assignment STATIC --static-ip-address-configuration IpAddress=192.168.26.87,NetMask=255.255.255.0 --launch-template-id s.lt-81d2c737e1adde32f --endpoint https://192.168.26.89 --profile snc89
      ```
      Reboot your snowcone and unlock it. A new Amazon Linux 2 image should be launched. This instance will autostart after reboot and unlocking.
   
2. Using OpsHub, create two 1TB volumes. Attach these volumes to your AL2 instance with the following Volume Device Names
      
      `/dev/sdh`
      
      `/dev/sdi`
      
3. dslakfj
4. 
