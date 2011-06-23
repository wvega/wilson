# Wordpress Skeleton #

A Fabric recipe to setup a new WordPress project and other common tasks

+ Download latest or specified version of WordPress
+ Create uploads directory
+ Add .htaccess file and remove wp-config-sample.php
+ Allows to create multiple wp-config.php files and switch between them.
+ Create DB backups using different blog URLs for each environment (local, testing and production)

# Using #

    git clone https://wvega@github.com/wvega/wordpress-skeleton.git
    fab setup
