# Readme for the Catalog App.

This application can be ran from the localhost at http://localhost:8000/ after running the following two commands to set up the database from the same folder as this Readme:

	1. python lotsofitem.py
	2. python project.py

There you should see a list of sports catagories and related items, as well as buttons to add items.  Clicking on an item name will navigate to that items page where you can modify or delete it. If you add "/json" at the end of any valid page you should get a back json formatted version of the information related to that page. 


Information related to this project below....


# OAuth2.0
Starter Code for Auth&amp;Auth course
# Installing the Vagrant VM for ud330 - Authentication & Authorization

**Note: If you already have a vagrant machine installed from previous Udacity courses skip to the 'Fetch the Source Code and VM Configuration' section**

In Lessons 2,3 and 4 of this course, you'll use a virtual machine (VM) to run a web server and a web app that uses it. The VM is a Linux system that runs on top of your own machine.  You can share files easily between your computer and the VM.

We're using the Vagrant software to configure and manage the VM. Here are the tools you'll need to install to get it running:

### Git

If you don't already have Git installed, [download Git from git-scm.com.](http://git-scm.com/downloads) Install the version for your operating system.

On Windows, Git will provide you with a Unix-style terminal and shell (Git Bash).  
(On Mac or Linux systems you can use the regular terminal program.)

You will need Git to install the configuration for the VM. If you'd like to learn more about Git, [take a look at our course about Git and Github](http://www.udacity.com/course/ud775).

### VirtualBox

VirtualBox is the software that actually runs the VM. [You can download it from virtualbox.org, here.](https://www.virtualbox.org/wiki/Downloads)  Install the *platform package* for your operating system.  You do not need the extension pack or the SDK. You do not need to launch VirtualBox after installing it.

**Ubuntu 14.04 Note:** If you are running Ubuntu 14.04, install VirtualBox using the Ubuntu Software Center, not the virtualbox.org web site. Due to a [reported bug](http://ubuntuforums.org/showthread.php?t=2227131), installing VirtualBox from the site may uninstall other software you need.

### Vagrant

Vagrant is the software that configures the VM and lets you share files between your host computer and the VM's filesystem.  [You can download it from vagrantup.com.](https://www.vagrantup.com/downloads) Install the version for your operating system.

**Windows Note:** The Installer may ask you to grant network permissions to Vagrant or make a firewall exception. Be sure to allow this.

## Fetch the Source Code and VM Configuration

**Windows:** Use the Git Bash program (installed with Git) to get a Unix-style terminal.  
**Other systems:** Use your favorite terminal program.

From the terminal, run:

    git clone https://github.com/udacity/OAuth2.0 oauth

This will give you a directory named **oauth** complete with the source code for the flask application, a vagrantfile, and a bootstrap.sh file for installing all of the necessary tools. 

## Run the virtual machine!

Using the terminal, change directory to oauth (**cd oauth**), then type **vagrant up** to launch your virtual machine.

