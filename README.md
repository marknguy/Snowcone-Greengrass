# Face detection using IoT Greengrass on Snowcone
AWS IoT Greengrass allows you to build, deploy, and manage device software to the Edge at-scale. In this demo, we show how IoT Greengrass manages an AI/ML model on Snowcone. The AI/ML model detects faces and draws rectangles around the eyes and face. This guide covers the building the on-premises portion of the architecture.

(contributions from Tim Wilhoit and Minh Bui. Thank you!)

## Architectural Overview
![Architectural Overview](gg-architecture.jpg)

### Requirements
- AWS Snowcone
- IP camera capable of outputting an MJPEG stream

### Assumptions
1. The Snowcone was ordered with the AWS IoT Greengrass validated AMI (amzn2-ami-snow-family-hvm-2.0.20210219.0-x86_64-gp2-b7e7f8d2-1b9e-4774-a374-120e0cd85d5a).
2. Familar with OpsHub and the SnowballEdge client. Both are installed on the user's computer. 
3. The SnowballEdge client has been configured with a profile using the appropriate Snowcone credentials.
4. AWS cli v2 has been installed and configured.


### Snowcone setup
1. Deploy an Amazon Linux 2 instance. The instance type should be snc1.medium. 

     (optional) - requires AWS cli for the `aws ec2 ...` command
   
      If you are setting up a long term demo, you can setup your instance to startup automatically after unlocking. The following autostart configuration sample works for Windows clients. Create a key pair in Opshub first if you don't already have one.
      First, create the launch template using aws cli. Make sure you replace `<ssh_key_name>` with your ssh key. Make sure you replace `<image_id>` with the image ID of your Amazon Linux 2 image. You can find the image ID using the command `aws ec2 describe-images --endpoint http://192.168.26.89:8008 --profile snc89 --region snow`. It will look something like this: `s.ami-8144e2b13711e662b`. The endpoint is the IP address of your snowcone.
      ```
      aws ec2 create-launch-template --launch-template-name al2-template --version-description version1 --launch-template-data "{\"ImageId\":\"<image_id>\",\"InstanceType\":\"snc1.medium\",\"KeyName\":\"<ssh_key_name>\"}" --endpoint http://192.168.26.89:8008 --profile snc89 --region snow
      ```
      Next, create the autostart configuration. Use the launch template ID from the previous command.
      ```
      snowballEdge create-autostart-configuration --physical-connector-type RJ45 --ip-address-assignment STATIC --static-ip-address-configuration IpAddress=192.168.26.87,NetMask=255.255.255.0 --launch-template-id s.lt-81d2c737e1adde32f --endpoint https://192.168.26.89 --profile snc89
      ```
      Reboot your snowcone and unlock it. A new Amazon Linux 2 image should be launched. This instance will autostart after reboot and unlocking.
   
2. Using OpsHub, create two 500GB volumes. Attach these volumes to your AL2 instance with the following Volume Device Names.
      
      `/dev/sdh`
      
      `/dev/sdi`
      
3. (optional) Use the `lsblk` command to view your available disk devices and their mount points (if applicable) to help you determine the correct device name to use. Since these are two newly added volumes, they will be `vda` and `vdb`.

     ```
     [ec2-user@ComputerVision ~]$ lsblk
     NAME     MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
     sda        8:0    0    8G  0 disk
     ├─sda1     8:1    0    8G  0 part /
     └─sda128 259:0    0    1M  0 part
     vda      253:0    0  500G  0 disk
     vdb      253:16   0  500G  0 disk
     ```
4. Create a file system of type xfs for each volume.

     ```
     sudo mkfs -t xfs /dev/vda
     sudo mkfs -t xfs /dev/vdb
     ```
5. Create two directories that will be our mount point for our new volumes.
     ```
     sudo mkdir /greengrass
     sudo mkdir /var/lib/docker
     ```

6. Mount the two new volumes at the newly created directories.
     ```
     sudo mount /dev/vda /greengrass
     sudo mount /dev/vdb /var/lib/docker
     ```
     verify they are mounted
     ```
     [ec2-user@ComputerVision ~]$ lsblk
     NAME     MAJ:MIN RM  SIZE RO TYPE MOUNTPOINT
     sda        8:0    0    8G  0 disk
     ├─sda1     8:1    0    8G  0 part /
     └─sda128 259:0    0    1M  0 part
     vda      253:0    0  500G  0 disk /greengrass
     vdb      253:16   0  500G  0 disk /var/lib/docker
     ```
7. Setup your automounts. This is done by editing the /etc/fstab.
     First, backup your `fstab` file.
     ```
     sudo cp /etc/fstab /etc/fstab.orig
     ```
     Determine the UUID of your new volumes. Note the UUID of `dev/vda`and `dev/vdb`.
     ```
     [ec2-user@ComputerVision ~]$ sudo blkid
     /dev/vda: UUID="f33b3c3d-2994-4674-8961-0e71e92f4421" TYPE="xfs"
     /dev/vdb: UUID="b979cae9-8914-48b1-8a18-dfb773141d43" TYPE="xfs"
     /dev/sda1: UUID="bc07e2f4-d5ff-494b-adf1-6f6da7608cd6" TYPE="xfs" PARTLABEL="Linux" PARTUUID="39cd914d-ca60-4f71-b1ca-a1d272387932"
     /dev/sda128: PARTLABEL="BIOS Boot Partition" PARTUUID="0e19dd44-e595-4daf-8567-e1bb121dcb2a"
     ```

8. Modify the `etc/fstab` by adding two lines to automount the two new volumes. Make sure to use your UUIDs, not the ones in this example.
     ```
     sudo sed -i '$ a UUID=f33b3c3d-2994-4674-8961-0e71e92f4421     /greengrass xfs    defaults,nofail   0   2' /etc/fstab
     sudo sed -i '$ a UUID=b979cae9-8914-48b1-8a18-dfb773141d43     /var/lib/docker xfs    defaults,nofail   0   2' /etc/fstab
     ```
9. Test your automounts.
     ```
     sudo umount /greengrass
     sudo umount /var/lib/docker
     sudo mount -a
     ```
     You should see `dev/vda` and `/dev/vdb` in the output of the `df -h` command.
     ```
     [ec2-user@ComputerVision ~]$ df -h
     Filesystem      Size  Used Avail Use% Mounted on
     devtmpfs        2.0G     0  2.0G   0% /dev
     tmpfs           2.0G     0  2.0G   0% /dev/shm
     tmpfs           2.0G  572K  2.0G   1% /run
     tmpfs           2.0G     0  2.0G   0% /sys/fs/cgroup
     /dev/sda1       8.0G  2.4G  5.7G  30% /
     /dev/vda        500G  8.9G  491G   2% /greengrass
     /dev/vdb        500G  8.1G  492G   2% /var/lib/docker
     ```
10. (ignore if using DHCP) Update your DNS server if you are using static VNIs.
     ```
     sudo sed -i 's/nameserver.*/nameserver 8.8.8.8/g' /etc/resolv.conf    
     ```
     Make the change persistent after reboot.
     ```
     sudo sed -i '$ a interface "eth0" {supersede domain-name-servers 8.8.4.4, 8.8.8.8;}' /etc/dhcp/dhclient.conf
     ```

10. Update your AL2 instance.

     ```
     sudo sed -i '$ a install_optional_items+=" grep "' /etc/dracut.conf.d/ec2.conf
     sudo yum update -y
     ```
     
11. Install Docker.

     ```
     sudo amazon-linux-extras install docker -y 
     sudo service docker start
     sudo systemctl enable docker
     ```
12. Install the Java runtime. We use the Amazon Corretto headless version because it includes bug fixes and omits unnecessary GUI components.
     ```
     sudo yum install java-11-amazon-corretto-headless -y
     ```
     
### Setup Snowcone as an IoT Greengrass core device.
This is from https://docs.aws.amazon.com/greengrass/v2/developerguide/quick-installation.html.

1. Grant root user permission to run the AWS IoT Greengrass software. Modify root permission from `root ALL=(ALL) ALL` to `root ALL=(ALL:ALL) ALL` in `sudoers` config file.
     ```
     sudo sed -in 's/root\tALL=(ALL)/root\tALL=(ALL:ALL)/' /etc/sudoers
     ```
     
2. Download the AWS IoT Greengrass core software.
     ```
     curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip -o greengrass-nucleus-latest.zip && 
     unzip greengrass-nucleus-latest.zip -d GreengrassInstaller && 
     rm greengrass-nucleus-latest.zip
     ```

3. Provide the credentials to allow you to install AWS IoT Greengrass Core software. Replace the values below with your credentials. These are credentials from the Region, not the Snow device.
     ```
     export AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
     export AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
     ```
4. Run the AWS IoT Greengrass Core installer. Replace argument values in your command as follows.
     - `region`. The AWS Region in which to find or create resources. Example `us-east-1`.
     - `MyGreengrassCore`. The name of the AWS IoT thing for your Greengrass core device. Example `Snowcone88`.
     - `MyGreengrassCoreGroup`. The name of AWS IoT thing group for your Greengrass core device. Example `FaceDetectors`.
     ```
     sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE \
       -jar ./GreengrassInstaller/lib/Greengrass.jar \
       --aws-region region \
       --thing-name MyGreengrassCore \
       --thing-group-name MyGreengrassCoreGroup \
       --thing-policy-name GreengrassV2IoTThingPolicy \
       --tes-role-name GreengrassV2TokenExchangeRole \
       --tes-role-alias-name GreengrassCoreTokenExchangeRoleAlias \
       --component-default-user ggc_user:ggc_group \
       --provision true \
       --setup-system-service true
     ```
     
### Build docker image and save to S3
1. Install git and clone this repository.
     ```
     sudo yum install git -y
     git clone https://github.com/marknguy/Snowcone-Greengrass/
     sudo usermod -aG docker ggc_user
     ```
2. Build the docker image and store it in the /greengrass volume
     ```
     cd ~/Snowcone-Greengrass/face_detection
     sudo DOCKER_BUILDKIT=1 docker build -t face_detection .
     sudo docker save -o /greengrass/face_detection.tar face_detection
     sudo chmod 644 /greengrass/face_detection.tar
     ```
3. Upload docker image to S3. 
     ```
     aws s3 cp /greengrass/face_detection.tar s3://<my_S3_bucket>/
     ```

### Create the necessary IAM policy and associate it to a role
1. Create a text filed called `component-artifact-policy.json` with the following contents. Use the name of your S3 bucket in place of `<my_S3_bucket>`.
     ```
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "s3:GetObject"
           ],
           "Resource": "arn:aws:s3:::<my_S3_bucket>/*"
         }
       ]
     }
     ```
2. Use the following command to create the IAM policy using the JSON file you just created.
     ```
     aws iam create-policy --policy-name MyGreengrassV2ComponentArtifactPolicy --policy-document file://component-artifact-policy.json
     ```
3. Attach your policy to the role, `GreengrassV2TokenExchangeRole`. The `<policy_arn>` is derived from the previous command.
     ```
     aws iam attach-role-policy --policy-arn <policy_arn> --role-name GreengrassV2TokenExchangeRole
     ```

### Create the component
1. Create a text filed called `com.example.FacialDetection.json` with the following contents. This is your component recipe. Use the name of your S3 bucket in place of `<my_S3_bucket>`. The mjpeg stream URL should go in `<MJPEG_STREAM_URL>`. Example: http://username:password@192.168.26.200/cgi-bin/mjpg/video.cgi?channel=1&subtype=1
     ```
     {
       "RecipeFormatVersion": "2020-01-25",
       "ComponentName": "com.example.FacialDetection",
       "ComponentVersion": "1.0.0",
       "ComponentType": "aws.greengrass.generic",
       "ComponentDescription": "A component that runs a Docker container from an image in an S3 bucket.",
       "ComponentPublisher": "Amazon",
       "Manifests": [
         {
           "Platform": {
             "os": "linux"
           },
           "Lifecycle": {
             "Install": {
               "Script": "docker load -i {artifacts:path}/face_detection.tar",
               "Timeout": "600"
             },
             "Run": {
               "Script": "docker run --rm --env PEOPLE_DETECTION_URL='<MJPEG_STREAM_URL>' --env LABELLED_STREAM_PORT=9000 -p 9000:9000 face_detection"
             }
           },
           "Artifacts": [
             {
               "Uri": "s3://<my_S3_bucket>/face_detection.tar"
             }
           ]
         }
       ],
       "Lifecycle": {}
     }
     ```
2. Install the AWS CLI version 2 so we can use Greengrass V2.
     ```
     curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
     unzip awscliv2.zip
     sudo ./aws/install
     ```
3. Create the greengrass component. The `<aws_region>` is your region. Ex: us-east-1.
     ```
     /usr/local/bin/aws greengrassv2 create-component-version --inline-recipe fileb://com.example.FacialDetection.json --region <aws_region>
     ```

### Create the deployment
1. Create a text filed called `deployment.json` with the following contents. Use your region and account ID for `<aws_region>` and `<aws_account_id>`, respectively. `<thing_group>` should be the name of your group of things, for example, `MyFaceDetectors`. `<deployment_name>` is a friendly name to call your deployment of this component to the group of IoT things.
     ```
     {
       "targetArn": "arn:aws:iot:<aws_region>:<aws_account_id>:thinggroup/<thing_group>",
       "deploymentName": "<deployment_name>",
       "components": {
         "com.example.FacialDetection": {
           "componentVersion": "1.0.0",
           "configurationUpdate": {}
         }
       },
       "deploymentPolicies": {
         "componentUpdatePolicy": {
           "action": "NOTIFY_COMPONENTS",
           "timeoutInSeconds": 30
         },
         "configurationValidationPolicy": {
           "timeoutInSeconds": 60
         },
         "failureHandlingPolicy": "ROLLBACK"
       }
     }
     ```
2. Create the deployment using your deployment template.
     ```
     /usr/local/bin/aws greengrassv2 create-deployment --cli-input-json file://deployment.json --region <region>
     ```
     
### Setup the webserver
1. Install apache.
     ```
     sudo yum install httpd -y
     sudo systemctl start httpd.service
     sudo systemctl enable httpd.service
     ```
     
2. Copy content over from the repository (already downloaded) and edit index.html to reflect the public IP address.
     ```
     sudo cp ~/Snowcone-Greengrass/html/* /var/www/html/
     sudo cp ~/Snowcone-Greengrass/gg-architecture.jpg /var/www/html/

     export PUBLIC_IP=`curl http://169.254.169.254/latest/meta-data/public-ipv4`
     sudo sed -i 's/127.0.0.1/'"$PUBLIC_IP"'/g' /var/www/html/index.html
     ```

### You should now be able to go `http://<IP_address_of_EC2_instance>` and see your demo!!! :)


### (alternative Easy method)
This procedure automates the process of setting up a Snowcone as an IoT Greengrass core device, building the docker image, creating the component, creating the deployment, and creating the webpage. Afterwards, you should be able to open a browser and see the demi This works on MacOS. 
Note: This stores your AWS credentials in the user-data. The user-data will be saved to /var/lib/cloud/instances/[instance-id]/user-data.txt. You may consider deleting this file once you have reviewed it.


1. Save this userdata file to your computer. Call it AL2_IOT_userdata.txt. Replace the following parameters appropriately.
     - `<presigned URL of manifest file>` Upload your manifest file to S3 and generate a presigned URL. This can be created within the S3 console.
     - `<snow_job_id>` This is the snow job id. Hint: same as the manifest file minus the _manifest.bin_. Ex: JID9be928de-c731-4167-bf23-752c0ffse8sde
     - `<unlock_code>` Unlock code of the Snow device. Example: cb587-0125d-caa70-87744-47382
     - `<ip_address_of_snow>` IP address of Snow device. Example: 192.168.26.89
     - `<aws_region>` AWS Region. Example: us-east-1.
     - `<iot_thing_name>` Thing name. Example: snowcone88.
     - `<thing_group_name>` Thing group. Example: FaceDetectors.
     - `<deployment-name>` Deployment name. Example: FaceDetector_on_Snow.
     - `<aws_access_key_id>` Access key ID from Region. Example: AKIA46OJAF6J4EXAMPLE
     - `<aws_secret_access_key>` Secret access key from Region. Example: 438BPatRMGohOiuCho9A6gGBLvEXAMPLE
     - `<existing_s3_bucket_in_region>` S3 bucket for storing docker container build
     - `<mjpeg_stream_url>` URL of the MJPEG stream. Example http://username:password@192.168.26.200/cgi-bin/mjpg/video.cgi?channel=1&subtype=1
  
     ```
     #!/bin/bash
     sleep 60
     export MANIFEST_URL="<presigned URL of manifest file>"
     export UNLOCK_CODE=<unlock_code>
     export SNOW_JOB_ID=<snow_job_id>
     export SNOW_IP=<ip_address_of_snow>
     export AWS_REGION=<aws_region>
     export IOT_THING_NAME=<iot_thing_name>
     export THING_GROUP=<thing_group_name>
     export DEPLOYMENT_NAME=<deployment_name>
     export AWS_ACCESS_KEY_ID=<aws_access_key_id>
     export AWS_SECRET_ACCESS_KEY=<aws_secret_access_key>
     export S3_BUCKET=<existing_s3_bucket_in_region>
     export STREAM_URL="<mjpeg_stream_url>"
     
     export MANIFEST_FILE=/home/ec2-user/.aws/snowball/config/mymanifest.bin
     sudo sed -i 's/nameserver.*/nameserver 8.8.8.8/g' /etc/resolv.conf 
     sudo sed -i '$ a interface "eth0" {supersede domain-name-servers 8.8.4.4, 8.8.8.8;}' /etc/dhcp/dhclient.conf 
     
     curl -s https://snowball-client.s3.us-west-2.amazonaws.com/latest/snowball-client-linux.tar.gz -o /home/ec2-user/sbe-client.tar.gz && cd /home/ec2-user &&
     tar -xf sbe-client.tar.gz
     export SBE_CLI_PATH=/home/ec2-user/`tar tf sbe-client.tar.gz | head -n1`bin

     mkdir .aws .aws/snowball .aws/snowball/config .aws/snowball/logs
     sudo mkdir /root/.aws /root/.aws/snowball /root/.aws/snowball/config /root/.aws/snowball/logs

     curl -s "$MANIFEST_URL" -o /home/ec2-user/.aws/snowball/config/mymanifest.bin
     sudo cp /home/ec2-user/.aws/snowball/config/mymanifest.bin /root/.aws/snowball/config/mymanifest.bin

     echo "{\"version\":1,\"profiles\":{\"snc89\":{\"name\":\"snc89\",\"jobId\":\"$SNOW_JOB_ID\",\"unlockCode\":\"$UNLOCK_CODE\",\"manifestPath\":\"/home/ec2-user/.aws/snowball/config/mymanifest.bin\",\"defaultEndpoint\":\"https://$SNOW_IP\"}}}" >> /home/ec2-user/.aws/snowball/config/snowball-edge.config

     sudo cp /home/ec2-user/.aws/snowball/config/snowball-edge.config /root/.aws/snowball/config/snowball-edge.config

     export SBE_ACCESS_KEY=`$SBE_CLI_PATH/snowballEdge list-access-keys --manifest-file $MANIFEST_FILE --unlock-code $UNLOCK_CODE --endpoint https://$SNOW_IP | grep AccessKeyIds | awk -F '"' '{print $4}'`

     $SBE_CLI_PATH/snowballEdge get-secret-access-key --access-key-id $SBE_ACCESS_KEY --manifest-file $MANIFEST_FILE --unlock-code $UNLOCK_CODE --endpoint https://$SNOW_IP >> /home/ec2-user/.aws/credentials

     sudo cp /home/ec2-user/.aws/credentials /root/.aws/credentials

     sudo chown -R ec2-user:ec2-user /home/ec2-user

     export GREENGRASS_VOLUME=`aws ec2 create-volume --availability-zone snow --volume-type "sbp1" --size 500 --profile snowballEdge --endpoint http://$SNOW_IP:8008 --region snow | grep VolumeId | awk -F '"' '{print $4}'`

     sleep 20

     export DOCKER_VOLUME=`aws ec2 create-volume --availability-zone snow --volume-type "sbp1" --size 500 --profile snowballEdge --endpoint http://$SNOW_IP:8008 --region snow | grep VolumeId | awk -F '"' '{print $4}'`

     sleep 30

     export INSTANCE_ID=`curl http://169.254.169.254/latest/meta-data/instance-id`

     aws ec2 attach-volume --instance-id $INSTANCE_ID --volume-id $GREENGRASS_VOLUME --device /dev/sdh --region snow --endpoint http://$SNOW_IP:8008 --profile snowballEdge
     sleep 20
     aws ec2 attach-volume --instance-id $INSTANCE_ID --volume-id $DOCKER_VOLUME --device /dev/sdi --region snow --endpoint http://$SNOW_IP:8008 --profile snowballEdge
     sleep 20
     
     sudo mkfs -t xfs /dev/vda
     sleep 10
     sudo mkfs -t xfs /dev/vdb

     sudo mkdir /greengrass
     sudo mkdir /var/lib/docker

     sudo mount /dev/vda /greengrass
     sleep 5
     sudo mount /dev/vdb /var/lib/docker

     export VDA_UUID=`sudo blkid | grep vda | awk -F '"' '{print $2}'`
     export VDB_UUID=`sudo blkid | grep vdb | awk -F '"' '{print $2}'`

     sudo sed -i "$ a UUID=$VDA_UUID     /greengrass xfs    defaults,nofail   0   2" /etc/fstab
     sudo sed -i "$ a UUID=$VDB_UUID     /var/lib/docker xfs    defaults,nofail   0   2" /etc/fstab

     sudo sed -i '$ a install_optional_items+=" grep "' /etc/dracut.conf.d/ec2.conf
     sudo yum update -y
     sudo amazon-linux-extras install docker -y 
     sudo service docker start
     sudo systemctl enable docker

     sudo yum install java-11-amazon-corretto-headless -y

     sudo sed -in 's/root\tALL=(ALL)/root\tALL=(ALL:ALL)/' /etc/sudoers

     curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip -o /home/ec2-user/greengrass-nucleus-latest.zip && cd /home/ec2-user &&
     unzip greengrass-nucleus-latest.zip -d GreengrassInstaller && 
     rm greengrass-nucleus-latest.zip

     sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE \
       -jar ./GreengrassInstaller/lib/Greengrass.jar \
       --aws-region $AWS_REGION \
       --thing-name $IOT_THING_NAME \
       --thing-group-name $THING_GROUP \
       --thing-policy-name GreengrassV2IoTThingPolicy \
       --tes-role-name GreengrassV2TokenExchangeRole \
       --tes-role-alias-name GreengrassCoreTokenExchangeRoleAlias \
       --component-default-user ggc_user:ggc_group \
       --provision true \
       --setup-system-service true
     
     sudo usermod -aG docker ggc_user
     sudo yum install git jq httpd -y
     git clone https://github.com/marknguy/Snowcone-Greengrass/
     
     cd ~/Snowcone-Greengrass/face_detection

     sudo DOCKER_BUILDKIT=1 docker build -t face_detection .
     sudo docker save -o /greengrass/face_detection.tar face_detection
     
     sudo chmod 644 /greengrass/face_detection.tar

     aws s3 cp /greengrass/face_detection.tar s3://$S3_BUCKET/
     
     cd

     jq -n --arg S3_BUCKET "$S3_BUCKET" '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["s3:GetObject"],"Resource":"arn:aws:s3:::'"$S3_BUCKET"'/*"}]}' > component-artifact-policy.json
     
     export GG_S3_POLICY=`aws iam create-policy --policy-name MyGreengrassV2ComponentArtifactPolicy --policy-document file://component-artifact-policy.json | grep Arn | awk -F '"' '{print $4}'`
     
     aws iam attach-role-policy --policy-arn $GG_S3_POLICY --role-name GreengrassV2TokenExchangeRole
     
     jq -n --arg S3_BUCKET "$S3_BUCKET" --arg SCRIPT "docker run --rm --env PEOPLE_DETECTION_URL='$STREAM_URL' --env LABELLED_STREAM_PORT=9000 -p 9000:9000 face_detection" $'{"RecipeFormatVersion": "2020-01-25","ComponentName": "com.example.FacialDetection","ComponentVersion":"1.0.0","ComponentType": "aws.greengrass.generic","ComponentDescription": "A component that runs a Docker container from an image in an S3 bucket.","ComponentPublisher": "Amazon","Manifests": [{"Platform": {"os": "linux"},"Lifecycle": {"Install": {"Script": "docker load -i {artifacts:path}/face_detection.tar","Timeout": "600"},"Run": {"Script": $SCRIPT}},"Artifacts": [{"Uri": "s3://'"$S3_BUCKET"'/face_detection.tar"}]}],"Lifecycle": {}}' > com.example.FacialDetection.json
     
     curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
     unzip awscliv2.zip
     sudo ./aws/install

     /usr/local/bin/aws greengrassv2 create-component-version --inline-recipe fileb://com.example.FacialDetection.json --region $AWS_REGION
     
     export AWS_ACCOUNT_ID=$(echo $GG_S3_POLICY | sed -n -e 's/^arn:aws:iam::\([0-9]\+\).*/\1/p')
     
     jq -n --arg AWS_REGION "$AWS_REGION" --arg AWS_ACCOUNT_ID "$AWS_ACCOUNT_ID" --arg THING_GROUP "$THING_GROUP" '{"targetArn": "arn:aws:iot:'"$AWS_REGION"':'"$AWS_ACCOUNT_ID"':thinggroup/'"$THING_GROUP"'","deploymentName":"'"$DEPLOYMENT_NAME"'","components": {"com.example.FacialDetection": { "componentVersion": "1.0.0","configurationUpdate": {}}},"deploymentPolicies": {"componentUpdatePolicy": { "action": "NOTIFY_COMPONENTS","timeoutInSeconds": 30},"configurationValidationPolicy": {"timeoutInSeconds": 60},"failureHandlingPolicy": "ROLLBACK"}}' > deployment.json
     
     /usr/local/bin/aws greengrassv2 create-deployment --cli-input-json file://deployment.json

     sudo cp ~/Snowcone-Greengrass/html/* /var/www/html/
     sudo cp ~/Snowcone-Greengrass/gg-architecture.jpg /var/www/html/
     
     export PUBLIC_IP=`curl http://169.254.169.254/latest/meta-data/public-ipv4`
     sudo sed -i 's/127.0.0.1/'"$PUBLIC_IP"'/g' /var/www/html/index.html
     sudo systemctl start httpd.service
     sudo systemctl enable httpd.service
     
     ```
2. Create a VNI. In the example below, s.ni-81de3334a74d29280 is physical interface ID. Replace this value with the physical interface id of your Snow device.
     ```
     export EC2_IP_ADDRESS=`snowballEdge create-virtual-network-interface --physical-network-interface-id s.ni-81de3334a74d29280 --ip-address-assignment DHCP --profile <my_snow_profile> | grep \"IpAddress\" | awk -F '"' '{print $4}'`
     ```
3. Launch your EC2 instance. In the example below, s.ami-8144e2b13711e662b is the image ID of the Amazon Linux 2 AMI on the Snow device. Replace this with your AMI ID on your Snow device. The instance type for a snowcone would be snc1.medium. The instance type for a snowball edge would be sbe-c.medium.
     ```
     export INSTANCE_ID=`aws ec2 run-instances --image-id s.ami-8144e2b13711e662b --count 1 --instance-type snc1.medium --key-name markngykp --user-data file://AL2_IOT_userdata.txt --endpoint http://192.168.26.89:8008 --profile sbe89 --region snow | grep InstanceId | awk -F '"' '{print $4}'` &&
     sleep 60 &&
     aws ec2 associate-address --instance-id $INSTANCE_ID --public-ip $EC2_IP_ADDRESS --profile sbe89 --endpoint http://192.168.26.89:8008 --region snow
     ```
