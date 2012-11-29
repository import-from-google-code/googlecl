#! /bin/bash

. utils.sh

# This test program manages contacts.

auth_username=$1

if [[ $1 == "" ]]; then
    echo "You have to provide username as the first parameter"
    exit
fi

blogname=$2

if [[ $2 == "" ]]; then
    echo "You have to provide blog name as the second parameter"
    exit
fi

cd "$(dirname $0)"
base_directory="$(pwd)"
googlecl_directory="$base_directory/../src"
gdata_directory="$base_directory/gdata_installs"

output_file="$base_directory/output.txt"


post_title="example post title" 
post_body="example post body"
post_tags="a,b"

touch $output_file

cd $gdata_directory

auth_executed=0

# $1 - number of expected blog posts
function check_posts_number {

    should_be \
        "./google blogger list --title \"$post_title\" --blog $blogname" \
        $1 \
        0 \
        "blog post" \
        "google blogger delete --title \"$post_title\" --blog $blogname"
        
}

for i in gdata-2.0.{1..17}
do

  echo -e '\n\n'
  echo "-----------------------------------------------------------------------" 
  echo "$i" 

  cd $gdata_directory/$i
  pwd
  
  export PYTHONPATH="$gdata_directory/$i/lib/python"
  echo "$PYTHONPATH" 

  cd $googlecl_directory
  pwd 
  
  if [[ $auth_executed == "0" ]]; then
    auth_executed=1 
    ./google blogger list --blog $blogname --force-auth -u $auth_username
  fi

  check_posts_number 0

  # Creating new blog post.
  ./google blogger post --title "$post_title" --blog $blogname "adlasdasd" 
  
  check_posts_number 1
  
  # Tagging the blog post, unfortunately there is no way to check if it worked.
  ./google blogger tag --blog $blogname --title "$post_title" --tags "$post_tags"
  
  # Deleting the blog post.
  ./google blogger delete --blog $blogname --title "$post_title"

  check_posts_number 0
  

done #>> $output_file