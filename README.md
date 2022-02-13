# Snowcone-Greengrass
AWS IoT Greengrass allows you to build, deploy, and manage device software to the Edge at-scale. In this demo, we show how IoT Greengrass manages an AI/ML model on Snowcone. Our AI/ML model detacts faces and draws rectangles around the eyes and face.

### Requirements
AWS Snowcone
IP camera capable of outputting an MJPEG stream

### Assumptions
1. The Snowcone was ordered with the AWS IoT Greengrass validated AMI (amzn2-ami-snow-family-hvm-2.0.20210219.0-x86_64-gp2-b7e7f8d2-1b9e-4774-a374-120e0cd85d5a).
2. Familar with OpsHub and the SnowballEdge client. Both are installed on the user's computer. 
3. The SnowballEdge client has been configured with a profile using the appropriate Snowcone credentials.


### Snowcone setup
1. Deploy an Amazon Linux 2 instance. The instance type should be snc1.medium. 

     (optional) - requires AWS cli for the `aws ec2 ...` command
   
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
12. Install the Java runtime. We use the Amazon Corretto headless version because it includes bug fixes and omits unnessary GUI components.
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

3. Provide the credentials to allow you to install AWS IoT Greengrass Core software. Replace the values below with your credentials.
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
     
### (althernative Easy method)

1. Save this userdata file to your computer. Call it AL2_IOT_userdata.txt. Edit the 
     ```
     #!/bin/bash
     sleep 90
     sudo sed -i 's/nameserver.*/nameserver 8.8.8.8/g' /etc/resolv.conf 
     sudo sed -i '$ a interface "eth0" {supersede domain-name-servers 8.8.4.4, 8.8.8.8;}' /etc/dhcp/dhclient.conf 
     sudo sed -i '$ a install_optional_items+=" grep "' /etc/dracut.conf.d/ec2.conf
     sudo yum update -y
     curl -s https://snowball-client.s3.us-west-2.amazonaws.com/latest/snowball-client-linux.tar.gz -o sbe-client.tar.gz && 
     tar -xf sbe-client.tar.gz
     export SBE_CLI_PATH=/home/ec2-user/`tar tf sbe-client.tar.gz | head -n1`bin
     mkdir .aws .aws/snowball .aws/snowball/config .aws/snowball/logs


     curl -s 'https://marknguyen.s3.us-east-1.amazonaws.com/JID9be928de-c731-4167-bf23-752c0ff463c2_manifest.bin?response-content-disposition=inline&X-Amz-Security-Token=IQoJb3JpZ2luX2VjEC4aCXVzLWVhc3QtMSJHMEUCIFSe8l8GHSMCkGNJ2FSKLegqTVpBcDHRWdiZ8NnZAxH1AiEAyz0wmKGPHKIXsVVMCCniX4M4%2BjapowISWBAWgMeOFHEq%2BwIIdxABGgw4OTAwMTY2NDA5MTUiDPZouBer8zau8hUgOCrYAhOrSJaGEk741z%2F0pXcfhreuVA%2FvMVHq%2BWeKBS41LDYtpfUm7R4UC89OufdQLc3YHCyiWaVgoPfaebkVnv%2Flm2EnaLbMmRMPF%2BchXguU%2BOKkRxUQxaAIP%2FcYGixacBUMA1LOsLyo7rVBRI72Fr9ZllEfsdAKmPeH5K%2Fr1xzykb%2Baoo9y%2BKO7LBRIOs7AvXBlVDFJkThxhRkexEYpF1frHWjUGcGGGwBwzsH%2FCRFPk%2BOsFlAIWFGsX1ctYXnMG1iobCecZXDKrua78PACzweLFCQr2Ltz8g8rlqs%2FU5Ot6dvOc%2Bhz6NWDwdYwa9RiUlXG2tSL%2F2raBfzOfMwor9DBgU6nYIW6bM4PL5DN6FHbCy1WubzDftYDKoQnxzYK1%2FF81eGbXW6eTL2OM%2FyL3qmKPbhLLO8SaZa2tnojSEa%2FciMgCbpfIvXI5FFEwL65bwX82XifMJeV%2Bn10MMiOpJAGOrMCbmuFu%2B4jBxFSvRhy7RJMlBHHZSlT6WJc1rfjToWyZrI93hol1xLFqoM345IniEi36Hq8jvW2ZJ8XhlxjXRy1rHLShPctu%2FfCgqme360%2FHRtC5WRUcCgSBI2WJa0w0lAGD0e3bBhELDvrZyAVWpd%2BXj4BkuAOVUnIuryeUj3Y2XgIiXVLZyUdly17MtIlYAyEikJun%2BpDYGCCSCewWrtEB58ofwcsh5xlOv0v0fYMYP%2FcubVKWnbV484JPbp762PAAK5SLCAIQum0eh3JNhJ%2Fcv46M2N1OBrbwPX804g2Uqqd4IeOjsVdmMutrvxslwpyLlVIjpikgPEDJ9su93FQl43Tr8y2G5Bv6IcWFIxYFQMvrlywP7Vpq8gQRs9%2BHs72Tm6IMYijXe29nwMQft1XfsAgfg%3D%3D&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Date=20220213T143532Z&X-Amz-SignedHeaders=host&X-Amz-Expires=10800&X-Amz-Credential=ASIA46OJAF6J3GS2IGWZ%2F20220213%2Fus-east-1%2Fs3%2Faws4_request&X-Amz-Signature=91e7772f16038816a2e9d42b53bda36a55a5044e10adede9c3af7ce06999e76b' -o $HOME/.aws/snowball/config/mymanifest.bin


     echo "{\"version\":1,\"profiles\":{\"snc89\":{\"name\":\"snc89\",\"jobId\":\"JID9be928de-c731-4167-bf23-752c0ff463c2\",\"unlockCode\":\"cb587-0125d-caa70-87744-79015\",\"manifestPath\":\"/home/ec2-user/.aws/snowball/config/mymanifest.bin\",\"defaultEndpoint\":\"https://192.168.26.89\"}}}" >> $HOME/.aws/snowball/config/snowball-edge.config


     export SBE_ACCESS_KEY=`$SBE_CLI_PATH/snowballEdge list-access-keys --profile snc89 | grep AccessKeyIds | awk -F '"' '{print $4}'`

     $SBE_CLI_PATH/snowballEdge get-secret-access-key --access-key-id $SBE_ACCESS_KEY --profile snc89 >> $HOME/.aws/credentials

     export GREENGRASS_VOLUME=`aws ec2 create-volume --availability-zone snow --volume-type "sbp1" --size 500 --profile snc89 --endpoint http://192.168.26.89:8008 | grep VolumeId | awk -F '"' '{print $4}'`

     export DOCKER_VOLUME=`aws ec2 create-volume --availability-zone snow --volume-type "sbp1" --size 500 --profile snc89 --endpoint http://192.168.26.89:8008 | grep VolumeId | awk -F '"' '{print $4}'`

     export INSTANCE_ID=`curl http://169.254.169.254/latest/meta-data/instance-id`

     aws ec2 attach-volume --instance-id $INSTANCE_ID --volume-id $GREENGRASS_VOLUME --device /dev/sdh --region snow --endpoint http://192.168.26.89:8008 --profile snc89
     aws ec2 attach-volume --instance-id $INSTANCE_ID --volume-id $DOCKER_VOLUME --device /dev/sdi --region snow --endpoint http://192.168.26.89:8008 --profile snc89

     sudo mkfs -t xfs /dev/vda
     sudo mkfs -t xfs /dev/vdb

     sudo mkdir /greengrass
     sudo mkdir /var/lib/docker

     export VDA_UUID=`sudo blkid | grep vda | awk -F '"' '{print $2}'`
     export VDB_UUID=`sudo blkid | grep vdb | awk -F '"' '{print $2}'`

     sudo sed -i "$ a UUID=$VDA_UUID     /greengrass xfs    defaults,nofail   0   2" /etc/fstab
     sudo sed -i "$ a UUID=$VDB_UUID     /greengrass xfs    defaults,nofail   0   2" /etc/fstab

     sudo mount -a

     sudo amazon-linux-extras install docker -y 
     sudo service docker start
     sudo systemctl enable docker

     sudo yum install java-11-amazon-corretto-headless -y

     sudo sed -in 's/root\tALL=(ALL)/root\tALL=(ALL:ALL)/' /etc/sudoers

     curl -s https://d2s8p88vqu9w66.cloudfront.net/releases/greengrass-nucleus-latest.zip -o greengrass-nucleus-latest.zip && 
     unzip greengrass-nucleus-latest.zip -d GreengrassInstaller && 
     rm greengrass-nucleus-latest.zip

     export AWS_ACCESS_KEY_ID=AKIA46OJAF6J4EXAMPLE
     export AWS_SECRET_ACCESS_KEY=438BPatRMGohOiuCho9A6gGBLvEXAMPLE

     sudo -E java -Droot="/greengrass/v2" -Dlog.store=FILE \
       -jar ./GreengrassInstaller/lib/Greengrass.jar \
       --aws-region us-east-1 \
       --thing-name SBE89 \
       --thing-group-name FaceDetectors \
       --thing-policy-name GreengrassV2IoTThingPolicy \
       --tes-role-name GreengrassV2TokenExchangeRole \
       --tes-role-alias-name GreengrassCoreTokenExchangeRoleAlias \
       --component-default-user ggc_user:ggc_group \
       --provision true \
       --setup-system-service true
     ```
2. Create a VNI.
     ```
     snowballEdge create-virtual-network-interface --physical-network-interface-id s.ni-81de3334a74d29280 --ip-address-assignment STATIC --static-ip-address-configuration IpAddress=192.168.26.94,Netmask=255.255.255.0 --profile sbe89
     ```
3. Launch your EC2 instance
     ```
     export INSTANCE_ID=`aws ec2 run-instances --image-id s.ami-8144e2b13711e662b --count 1 --instance-type sbe-c.medium --key-name markngykp --user-data file://auto-build-iot-greengrass.txt --endpoint http://192.168.26.89:8008 --profile sbe89 --region snow | grep InstanceId | awk -F '"' '{print $4}'` &&
     aws ec2 associate-address --instance-id $INSTANCE_ID --public-ip 192.168.26.94 --profile snowballEdge --endpoint http://192.168.26.89:8008 --region snow
     ```
