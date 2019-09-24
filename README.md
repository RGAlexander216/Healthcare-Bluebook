> This project requires python 3.7 as some some features implemented within this project 
> utilize only currently available in this version

> To run the script simply open a command promt and navigate to the directory
> in which this file is found. Then run the commands:

> to ensure that you have the necessary packages you can optionally run this first

pip install -r requirements.txt

> Then start the main script by running the next line. Note that if you don't
> provide an exact match you will be prompted to enter the ID of the procedure
> to retrieve data for. 

Python Requester.py --search_term MRI --search_type Procedure --search_zip 37221 

> This will output all the data for the "green" locations for whichever procedure
> is provided into an XLSX file held in the Results folder
> downloaded/created by running the above command.
