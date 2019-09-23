> This project requires python 3.7 as some some features implemented within this project 
> utilize only currently available in this version

> To run the script simply open a command promt and navigate to the directory
> in which this file is found. Then run the commands:

> to ensure that you have the necessary packages you can optionally run this first

pip install -r requirements.txt

> Then start the main script by running the next line

Python Requester.py --search_term MRI --search_type Procedure --search_zip 37221 

> You'll see output of the URLs and some of the JSON response output

> ################################################################################

> Alternatively, you can run the Selenium Version as seen below:

Python SeleniumVersion.py --search_term MRI --search_type Procedure --search_zip 37221
