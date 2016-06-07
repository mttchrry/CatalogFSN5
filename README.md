Linux Server Full Stack Nano Degree Project 7 README.

This Catalog website is being served at 52.35.8.178 on port 2200 with full functionality.
The public address is http://ec2-52-35-8-178.us-west-2.compute.amazonaws.com/

Software installed on the linux server includes apache2, postgresql, and Git.

Configurations included changing the apache .wsgi file to point to my app obtained via
git, changes to deny remote login with the root user via /etc/ssh/sshd_config, the creation
of grader and catalog users, and giving grader sudo access. I also changed to the UFW to
only allow  ports 2200, 80, and 123.  In PostgreSQL I created a catalog user to enable creation
and modification of database objects on the database "catalog". 

Resource I used to complete this project were the Udacity Forums, the tutorial at Digital Ocean
https://www.digitalocean.com/community/tutorials/how-to-deploy-a-flask-application-on-an-ubuntu-vps
as well as http://docs.sqlalchemy.org/en/rel_1_0/core/engines.html#postgresql for converting
over my sqlite database to postgresql.  

